import csv
import logging
import time
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Count
from django.db import DatabaseError
from django.utils import timezone
from .models import Event
from .detector import analyze
logger=logging.getLogger(__name__)

@ensure_csrf_cookie
def home(request):
    if not request.session.session_key: request.session.create()
    return render(request,'vision/home.html')

@require_POST
def frame(request):
    if not request.session.session_key:
        return JsonResponse({'error':'Recarga la página antes de iniciar.'},status=400)
    if request.content_type != 'image/jpeg' or not (0<len(request.body)<=400000):
        return JsonResponse({'error':'Envía una imagen JPEG de hasta 400 KB.'},status=400)
    now=time.time()
    if now-request.session.get('last_frame',0)<0.08:
        return JsonResponse({'error':'Demasiadas solicitudes. Intenta nuevamente.'},status=429)
    request.session['last_frame']=now
    try:
        result=analyze(request.body, render_image=False)
    except ValueError as exc:
        return JsonResponse({'error':str(exc)},status=400)
    except FileNotFoundError as exc:
        return JsonResponse({'error':str(exc)},status=503)
    except Exception:
        logger.exception('Error procesando imagen')
        return JsonResponse({'error':'No se pudo iniciar el detector. Revisa la terminal del servidor.'},status=503)
    signature=' + '.join(sorted(h['gesture'] for h in result['hands']))
    state=request.session.get('candidate',{})
    # Require 3 consecutive matching frames. Store only transitions; re-arm after no hands.
    count=state.get('count',0)+1 if state.get('signature')==signature else 1
    request.session['candidate']={'signature':signature,'count':min(count,3)}
    saved=False
    if not signature:
        request.session['last_signature']=''
    elif count>=3 and signature!=request.session.get('last_signature') and now-request.session.get('last_saved',0)>=2:
        try:
            Event.objects.create(session_key=request.session.session_key,gesture=signature,fingers=result['total'],hands=len(result['hands']))
            request.session['last_signature']=signature
            request.session['last_saved']=now
            saved=True
        except DatabaseError:
            result['warning']='No se pudo guardar el evento. Revisa PostgreSQL.'
    result['saved']=saved
    return JsonResponse(result)

@require_GET
def history(request):
    events=Event.objects.filter(session_key=request.session.session_key or '')
    return JsonResponse({'count':events.count(),'top':list(events.values('gesture').annotate(count=Count('id')).order_by('-count')[:5]),'events':[{'time':timezone.localtime(e.created_at).strftime('%d/%m %H:%M:%S'),'gesture':e.gesture,'fingers':e.fingers,'hands':e.hands} for e in events[:30]]})

@require_GET
def export_csv(request):
    response=HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition']='attachment; filename="manovision_eventos.csv"'
    response.write('\ufeff')
    writer=csv.writer(response)
    writer.writerow(['Fecha','Gesto','Dedos','Manos'])
    for e in Event.objects.filter(session_key=request.session.session_key or '').iterator():
        writer.writerow([timezone.localtime(e.created_at).isoformat(),e.gesture,e.fingers,e.hands])
    return response
