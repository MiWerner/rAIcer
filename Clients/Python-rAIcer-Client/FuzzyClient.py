import sys

sys.argv.append("--speed")
sys.argv.append("--cp_ids")
sys.argv.append("1")

import RaicerSocket
from Utils import S_WAIT, S_COUNTDOWN, S_RUNNING, S_FINISHED, S_CRASHED, S_CANCELED, print_debug
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from Features import FeatureCalculator
import time

# build fuzzy logic

# Antecedents
s_h = ctrl.Antecedent(np.arange(-30, 31, .1), 'speed h')
s_h['fast left'] = fuzz.trimf(s_h.universe, [-30, -30, -10])
s_h['medium left'] = fuzz.trimf(s_h.universe, [-15, -10, -5])
s_h['slow left'] = fuzz.trimf(s_h.universe, [-10, -1, 0])
s_h['slow'] = fuzz.trimf(s_h.universe, [-1, 0, 1])
s_h['slow right'] = fuzz.trimf(s_h.universe, [0, 1, 10])
s_h['medium right'] = fuzz.trimf(s_h.universe, [5, 10, 15])
s_h['fast right'] = fuzz.trimf(s_h.universe, [10, 30, 30])

s_v = ctrl.Antecedent(np.arange(-30, 31, .1), 'speed v')
s_v['fast up'] = fuzz.trimf(s_h.universe, [-30, -30, -10])
s_v['medium up'] = fuzz.trimf(s_h.universe, [-15, -10, -5])
s_v['slow up'] = fuzz.trimf(s_h.universe, [-10, -1, 0])
s_v['slow'] = fuzz.trimf(s_v.universe, [-1, 0, 1])
s_v['slow down'] = fuzz.trimf(s_h.universe, [0, 1, 10])
s_v['medium down'] = fuzz.trimf(s_h.universe, [5, 10, 15])
s_v['fast down'] = fuzz.trimf(s_h.universe, [10, 30, 30])

d_h = ctrl.Antecedent(np.arange(-512, 513, .1), 'dist h')
d_h['far left'] = fuzz.trimf(d_h.universe, [-512, -512, -50])
d_h['medium left'] = fuzz.trimf(d_h.universe, [-100, -50, -10])
d_h['short left'] = fuzz.trimf(d_h.universe, [-20, -5, 0])
d_h['close'] = fuzz.trimf(d_h.universe, [-5, 0, 5])
d_h['short right'] = fuzz.trimf(d_h.universe, [0, 5, 20])
d_h['medium right'] = fuzz.trimf(d_h.universe, [10, 50, 100])
d_h['far right'] = fuzz.trimf(d_h.universe, [50, 512, 512])


d_v = ctrl.Antecedent(np.arange(-512, 513, .1), 'dist v')
d_v['far up'] = fuzz.trimf(d_v.universe, [-512, -512, -50])
d_v['medium up'] = fuzz.trimf(d_v.universe, [-100, -50, -10])
d_v['short up'] = fuzz.trimf(d_v.universe, [-20, -5, 0])
d_v['close'] = fuzz.trimf(d_v.universe, [-5, 0, 5])
d_v['short down'] = fuzz.trimf(d_v.universe, [0, 5, 20])
d_v['medium down'] = fuzz.trimf(d_v.universe, [10, 50, 100])
d_v['far down'] = fuzz.trimf(d_v.universe, [50, 512, 512])

# Consequents
k_up = ctrl.Consequent(np.arange(0, 2, 1), 'key up')
k_up['press'] = fuzz.trimf(k_up.universe, [0, 1, 1])
k_up['nopress'] = fuzz.trimf(k_up.universe, [0, 0, 1])

k_down = ctrl.Consequent(np.arange(0, 2, 1), 'key down')
k_down['press'] = fuzz.trimf(k_down.universe, [0, 1, 1])
k_down['nopress'] = fuzz.trimf(k_down.universe, [0, 0, 1])

k_left = ctrl.Consequent(np.arange(0, 2, 1), 'key left')
k_left['press'] = fuzz.trimf(k_left.universe, [0, 1, 1])
k_left['nopress'] = fuzz.trimf(k_left.universe, [0, 0, 1])

k_right = ctrl.Consequent(np.arange(0, 2, 1), 'key right')
k_right['press'] = fuzz.trimf(k_right.universe, [0, 1, 1])
k_right['nopress'] = fuzz.trimf(k_right.universe, [0, 0, 1])

# rules
rules = []

rules.append(ctrl.Rule(d_h['short right'] & (s_h['slow right'] | s_h['slow'] | s_h['slow left'] | s_h['medium left'] | s_h['fast left']), k_right['press']))
rules.append(ctrl.Rule(d_h['medium right'] & (s_h['medium right'] | s_h['slow'] | s_h['slow right'] | s_h['slow left'] | s_h['medium left'] | s_h['fast left']), k_right['press']))
rules.append(ctrl.Rule(d_h['far right'] & (s_h['medium right'] | s_h['slow'] | s_h['slow right'] | s_h['slow left'] | s_h['medium left'] | s_h['fast left']), k_right['press']))
rules.append(ctrl.Rule(s_h['fast right'], k_right['nopress']))

rules.append(ctrl.Rule(d_h['short left'] & (s_h['slow left'] | s_h['slow'] | s_h['slow right'] | s_h['medium right'] | s_h['fast right']), k_left['press']))
rules.append(ctrl.Rule(d_h['medium left'] & (s_h['medium left'] | s_h['slow'] | s_h['slow left'] | s_h['slow right'] | s_h['medium right'] | s_h['fast right']), k_left['press']))
rules.append(ctrl.Rule(d_h['far left'] & (s_h['medium left'] | s_h['slow'] | s_h['slow left'] | s_h['slow right'] | s_h['medium right'] | s_h['fast right']), k_left['press']))
rules.append(ctrl.Rule(s_h['fast left'], k_left['nopress']))

rules.append(ctrl.Rule(d_v['short up'] & (s_v['slow up'] | s_h['slow'] | s_v['slow down'] | s_v['medium down'] | s_v['fast down']), k_up['press']))
rules.append(ctrl.Rule(d_v['medium up'] & (s_v['medium up'] | s_h['slow'] | s_v['slow up'] | s_v['slow down'] | s_v['medium down'] | s_v['fast down']), k_up['press']))
rules.append(ctrl.Rule(d_v['far up'] & (s_v['medium up'] | s_h['slow'] | s_v['slow up'] | s_v['slow down'] | s_v['medium down'] | s_v['fast down']), k_up['press']))
rules.append(ctrl.Rule(s_v['fast up'], k_up['nopress']))

rules.append(ctrl.Rule(d_v['short down'] & (s_v['slow down'] | s_h['slow'] | s_v['slow up'] | s_v['medium up'] | s_v['fast up']), k_down['press']))
rules.append(ctrl.Rule(d_v['medium down'] & (s_v['medium down'] | s_h['slow'] | s_v['slow down'] | s_v['slow up'] | s_v['medium up'] | s_v['fast up']), k_down['press']))
rules.append(ctrl.Rule(d_v['far down'] & (s_v['medium down'] | s_h['slow'] | s_v['slow down'] | s_v['slow up'] | s_v['medium up'] | s_v['fast up']), k_down['press']))
rules.append(ctrl.Rule(s_v['fast down'], k_down['nopress']))

keys_ctrl = ctrl.ControlSystem(rules)
keys = ctrl.ControlSystemSimulation(keys_ctrl)

fc = None
s = RaicerSocket.RaicerSocket()
s.connect()

status = -1
try:
    while 1:

        if s.new_message:
            ID, status, lap_id, lap_total, damage, rank, image = s.receive()
            if fc is not None:
                fc.update(img=image, print_features=True)

        if status == S_RUNNING:
            features = fc.features
            keys.input['speed h'] = features[0]
            keys.input['speed v'] = features[1]
            keys.input['dist h'] = features[2]
            keys.input['dist v'] = features[3]


            keys.compute()
            s.send_key_msg(keys.output['key up'],
                           keys.output['key down'],
                           keys.output['key left'],
                           keys.output['key right'])

        elif status == S_COUNTDOWN:
            if fc is None:
                fc = FeatureCalculator(img=image, client_id=ID)

            time.sleep(0.1)
        elif status == S_WAIT:
            pass
        elif status == S_FINISHED:
            print_debug('Finished!')
            break

        elif status == S_CRASHED:
            print_debug('Crashed')
            break

        elif status == S_CANCELED:
            print_debug('Canceled')
            break

        time.sleep(.1)
finally:
    s.close()
