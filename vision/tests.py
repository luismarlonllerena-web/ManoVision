from unittest.mock import patch
from django.test import TestCase, Client
from .models import Event
from .gestures import classify, angle, finger_states
from django.test import SimpleTestCase
from .detector import analyze as real_analyze

class DetectorInputTests(SimpleTestCase):
    def test_invalid_payloads(self):
        for payload in (b'', b'not jpeg', b'\x89PNG\r\n\x1a\n'):
            with self.assertRaises(ValueError):
                real_analyze(payload)

class GestureTests(TestCase):
    def test_labels(self):
        points=[(0,0,0)]*21
        for states,label in [([1]*5,'Mano abierta'),([0]*5,'Puño'),([0,1,1,0,0],'Victoria'),([0,1,0,0,0],'Índice')]:
            self.assertEqual(classify(states,points),label)
    def test_angles(self):
        self.assertAlmostEqual(angle((0,0),(1,0),(2,0)),180)
        self.assertAlmostEqual(angle((0,0),(1,0),(1,1)),90)
    def test_collapsed(self):
        self.assertEqual(finger_states([(0,0,0)]*21),[False]*5)
    def test_rotation(self):
        p=[(0.,0.,0.) for _ in range(21)]
        for start,x in [(5,-1.5),(9,-.5),(13,.5),(17,1.5)]:
            for offset in range(4):p[start+offset]=(x,2.+offset,0.)
        self.assertEqual(finger_states(p)[1:],[True]*4)
        self.assertEqual(finger_states([(-y,x,z) for x,y,z in p]),finger_states(p))

class APITests(TestCase):
    def setUp(self):self.client.get('/')
    def test_home(self):
        self.assertContains(self.client.get('/'),'ManoVision')
        self.assertEqual(self.client.get('/api/history/').json()['count'],0)
    def test_invalid_request(self):
        self.assertEqual(self.client.post('/api/frame/',b'bad',content_type='text/plain').status_code,400)
        self.assertEqual(self.client.get('/api/frame/').status_code,405)
    @patch('vision.views.analyze',side_effect=ValueError('Imagen inválida'))
    def test_bad_image(self,mock):
        self.assertEqual(self.client.post('/api/frame/',b'bad',content_type='image/jpeg').status_code,400)
    @patch('vision.views.analyze',side_effect=FileNotFoundError('Falta modelo'))
    def test_missing_model(self,mock):
        self.assertEqual(self.client.post('/api/frame/',b'jpg',content_type='image/jpeg').status_code,503)
    @patch('vision.views.time.time')
    @patch('vision.views.analyze')
    def test_stability_dedup_and_reentry(self,analyze,clock):
        hand={'hands':[{'gesture':'Victoria','fingers':2}],'total':2,'image':''}
        for i in range(6):
            clock.return_value=1000+i;analyze.return_value=dict(hand)
            self.assertEqual(self.client.post('/api/frame/',b'jpg',content_type='image/jpeg').status_code,200)
        self.assertEqual(Event.objects.count(),1)
        clock.return_value=1010;analyze.return_value={'hands':[],'total':0,'image':''}
        self.client.post('/api/frame/',b'jpg',content_type='image/jpeg')
        for i in range(3):
            clock.return_value=1020+i;analyze.return_value=dict(hand)
            self.client.post('/api/frame/',b'jpg',content_type='image/jpeg')
        self.assertEqual(Event.objects.count(),2)
    def test_session_isolation_csv(self):
        Event.objects.create(session_key=self.client.session.session_key,gesture='Puño',fingers=0,hands=1)
        other=Client();other.get('/')
        self.assertEqual(other.get('/api/history/').json()['count'],0)
        self.assertEqual(self.client.get('/api/history/').json()['count'],1)
        self.assertIn('Puño',self.client.get('/exportar/').content.decode())
        self.assertNotIn('Puño',other.get('/exportar/').content.decode())
    def test_csrf(self):
        client=Client(enforce_csrf_checks=True);client.get('/')
        self.assertEqual(client.post('/api/frame/',b'jpg',content_type='image/jpeg').status_code,403)

    @patch('vision.views.time.time')
    @patch('vision.views.analyze')
    def test_two_hands_stats_and_csv(self, analyze, clock):
        analyze.return_value={'hands':[{'gesture':'Mano abierta','fingers':5}]*2,'total':10,'image':''}
        for i in range(3):
            clock.return_value=2000+i
            response=self.client.post('/api/frame/',b'jpg',content_type='image/jpeg')
        self.assertTrue(response.json()['saved'])
        event=Event.objects.get()
        self.assertEqual((event.fingers,event.hands),(10,2))
        data=self.client.get('/api/history/').json()
        self.assertEqual(data['top'][0]['count'],1)
        self.assertIn('Mano abierta + Mano abierta,10,2', self.client.get('/exportar/').content.decode('utf-8-sig'))

    @patch('vision.views.time.time', return_value=3000)
    @patch('vision.views.analyze', return_value={'hands':[],'total':0,'image':''})
    def test_rate_limit(self, analyze, clock):
        self.client.post('/api/frame/',b'jpg',content_type='image/jpeg')
        self.assertEqual(self.client.post('/api/frame/',b'jpg',content_type='image/jpeg').status_code,429)
