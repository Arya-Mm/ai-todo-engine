import json
import random
import os
import numpy as np

Q_PATH = "q_table.json"

ACTIONS = [0.5, 1, 2, 3, 4, 5]

ALPHA = 0.1      # learning rate
GAMMA = 0.9      # discount factor
EPSILON = 0.1    # exploration rate


# --------------------------------------------------
# LOAD / SAVE Q TABLE
# --------------------------------------------------

def load_q():
    if not os.path.exists(Q_PATH):
        return {}

    with open(Q_PATH, "r") as f:
        return json.load(f)


def save_q(q_table):
    with open(Q_PATH, "w") as f:
        json.dump(q_table, f)


q_table = load_q()


# --------------------------------------------------
# STATE HANDLING
# --------------------------------------------------

def normalize_state(embedding):
    rounded = tuple(round(float(x), 2) for x in embedding)
    return str(rounded)


# --------------------------------------------------
# ACTION SELECTION (ε-greedy)
# --------------------------------------------------

def choose_action(embedding, max_capacity):

    state_key = normalize_state(embedding)

    if random.random() < EPSILON:
        # explore
        return random.choice(ACTIONS)

    # exploit
    if state_key not in q_table:
        q_table[state_key] = {str(a): 0 for a in ACTIONS}

    state_actions = q_table[state_key]

    best_action = max(state_actions, key=state_actions.get)
    return min(float(best_action), max_capacity)


# --------------------------------------------------
# Q UPDATE (TD LEARNING)
# --------------------------------------------------

def update_q(prev_embedding, action, reward, next_embedding):

    prev_key = normalize_state(prev_embedding)
    next_key = normalize_state(next_embedding)

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
