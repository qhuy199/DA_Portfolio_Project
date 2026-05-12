import numpy as np
import pandas as pd 
def generate_random_number():
    return np.random.randint(1, 100, size=10)

def sort_random_number():
    random_number = generate_random_number()
    return np.sort(random_number)
def print_random_number():
    random_number = generate_random_number()
    print(random_number)
def print_sort_random_number():
    sort_random_number = sort_random_number()
    print(sort_random_number)
print_sort_random_number()              

