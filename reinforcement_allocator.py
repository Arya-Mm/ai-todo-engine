import numpy as np
import pickle
import os
import random

# ==================================================
# CONFIG
# ==================================================

MODEL_PATH = "td_function_model.pkl"

ALPHA = 0.01      # learning rate
GAMMA = 0.95      # discount factor
EPSILON = 0.15    # exploration rate

ACTION_SPACE = [0.5, 1, 2, 3, 4, 5]  # possible hour allocations


# ==================================================
# MODEL LOAD / INIT
# ==================================================

def load_model():
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    else:
        # initialize small random weights
        return np.random.randn(16) * 0.01


def save_model(weights):
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(weights, f)


weights = load_model()


# ==================================================
# FEATURE CONSTRUCTION φ(s,a)
# ==================================================

def build_features(embedding, action):
    """
    Combine state embedding and action into feature vector.
    """

    action_vector = np.array([action, action ** 2])

    return np.concatenate([embedding, action_vector])


# ==================================================
# Q VALUE
# ==================================================

def q_value(embedding, action):
    features = build_features(embedding, action)
    return np.dot(weights, features)


# ==================================================
# POLICY
# ==================================================

def choose_allocation(embedding, max_capacity):

    # ε-greedy exploration
    if random.random() < EPSILON:
        return random.choice(ACTION_SPACE)

    # exploit
    q_values = []

    for a in ACTION_SPACE:
        if a <= max_capacity:
            q_values.append((a, q_value(embedding, a)))

    if not q_values:
        return None

    best_action = max(q_values, key=lambda x: x[1])[0]

    return best_action


# ==================================================
# TD UPDATE
# ==================================================

def td_update(prev_embedding, action, reward, next_embedding):

    global weights

    prev_features = build_features(prev_embedding, action)

    # Current Q
    current_q = np.dot(weights, prev_features)

    # Next max Q
    next_q_values = [
        q_value(next_embedding, a) for a in ACTION_SPACE
    ]

    max_next_q = max(next_q_values) if next_q_values else 0

    # TD target
    target = reward + GAMMA * max_next_q

    td_error = target - current_q

    # Gradient update
    weights += ALPHA * td_error * prev_features

    save_model(weights)
