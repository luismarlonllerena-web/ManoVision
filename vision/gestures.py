"""Geometric heuristics on 21 landmarks; not a sign-language translator.
Angles and wrist distance make counting less dependent on camera rotation.
Thumb thresholds remain approximate, especially with occlusion or side views.
"""
import math

def distance(a,b):
    return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))

def angle(a,b,c):
    u=[x-y for x,y in zip(a,b)]; v=[x-y for x,y in zip(c,b)]
    denominator=math.sqrt(sum(x*x for x in u)*sum(x*x for x in v))
    if denominator < 1e-9: return 0
    return math.degrees(math.acos(max(-1,min(1,sum(x*y for x,y in zip(u,v))/denominator))))

def finger_states(points):
    thumb = (angle(points[1],points[2],points[3]) > 145 and
             angle(points[2],points[3],points[4]) > 150 and
             distance(points[4],points[17]) > distance(points[3],points[17])*1.15)
    states=[thumb]
    for mcp,pip,dip,tip in [(5,6,7,8),(9,10,11,12),(13,14,15,16),(17,18,19,20)]:
        states.append(angle(points[mcp],points[pip],points[tip])>155 and
                      angle(points[pip],points[dip],points[tip])>150 and
                      distance(points[tip],points[0])>distance(points[pip],points[0])*1.12)
    return states

def classify(states,points):
    if all(states): return 'Mano abierta'
    if not any(states): return 'Puño'
    if states == [False,True,True,False,False]: return 'Victoria'
    if states == [False,True,False,False,False]: return 'Índice'
    if states == [True,False,False,False,False]:
        if points[4][1] < points[2][1]: return 'Pulgar arriba'
        return 'Pulgar extendido'
    return f'{sum(states)} dedos'
