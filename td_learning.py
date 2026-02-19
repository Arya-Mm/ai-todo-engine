import json
import os
import random

Q_PATH = "q_table.json"

ACTIONS = [0.5, 1, 2, 3, 4, 5]

ALPHA = 0.1
GAMMA = 0.9
EPSILON = 0.1


def load_q():
    if not os.path.exists(Q_PATH):
        return {}

    with open(Q_PATH, "r") as f:
        return json.load(f)


def save_q(q_table):
    with open(Q_PATH, "w") as f:
        json.dump(q_table, f)


q_table = load_q()


def normalize_state(state_tuple):
    return str(tuple(round(float(x), 2) for x in state_tuple))


def choose_action(state_tuple, max_capacity):

    state_key = normalize_state(state_tuple)

    if random.random() < EPSILON:
        return random.choice(ACTIONS)

    if state_key not in q_table:
        q_table[state_key] = {str(a): 0 for a in ACTIONS}

    best_action = max(q_table[state_key], key=q_table[state_key].get)

    return min(float(best_action), max_capacity)


def update_q(prev_state, action, reward, next_state):

    prev_key = normalize_state(prev_state)
    next_key = normalize_state(next_state)

    if prev_key not in q_table:
        q_table[prev_key] = {str(a): 0 for a in ACTIONS}

    if next_key not in q_table:
        q_table[next_key] = {str(a): 0 for a in ACTIONS}

    current_q = q_table[prev_key][str(action)]
    max_next_q = max(q_table[next_key].values())

    new_q = current_q + ALPHA * (
        reward + GAMMA * max_next_q - current_q
    )

    q_table[prev_key][str(action)] = new_q

    save_q(q_table)
