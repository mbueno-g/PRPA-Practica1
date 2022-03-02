from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore, Lock
from multiprocessing import current_process
from multiprocessing import Value, Array
from time import sleep
from random import random, randint
import numpy as np


N = 4 # numero de elementos que genera el productor
K = 10 # tamaño del buffer de cada productor
NPROD = 3
NCONS = 1

def delay(factor = 3):
    sleep(random()/factor)


def add_data(storage, index, data, mutex):
    mutex.acquire()
    try:
        storage[index.value] = data
        delay(6)
        index.value = index.value + 1
    finally:
        mutex.release()


def get_data(storage, index, mutex):
    mutex.acquire()
    try:
        data = storage[0]
        index.value = index.value - 1
        delay()
        for i in range(index.value):
            storage[i] = storage[i + 1]
        storage[index.value] = -1
    finally:
        mutex.release()


def producer(storage, index, empty, non_empty, mutex):
    data = randint(0,10)
    for v in range(N):
        print (f"producer {current_process().name} produciendo")
        delay(6)
        empty.acquire()
        data += randint(0,10)
        add_data(storage, index, data, mutex)
        non_empty.release()
        print (f"producer {current_process().name} almacenado {data}")
    empty.acquire()
    add_data(storage,index, -1, mutex)
    non_empty.release()
    print (f"producer {current_process().name} almacenado {-1}")


def haya_productores(storage):
    for i in range(NPROD):
        if (storage[i][0] != -1):
            return True
    return False


def get_min(storage, index, mutex):
    mini = []
    ind = []
    for i in range(NPROD):
        if (storage[i][0] != -1):
            mini.append(storage[i][0])
            ind.append(i)
    k = np.argmin(mini)
    return ind[k], mini[k]


def consumer(storage, index, empty, non_empty, mutex, sorted_data):
    for v in range(NPROD):
        non_empty[v].acquire()
    i = 0
    while haya_productores(storage):
        print (f"consumer {current_process().name} desalmacenando")
        ind, value = get_min(storage, index, mutex)
        if (value != -1):
            get_data(storage[ind], index[ind], mutex[ind])
            sorted_data[i] = value
            empty[ind].release()
            non_empty[ind].acquire()
            print (f"consumer {current_process().name} consumiendo {value} del producer {ind}")
            delay()
        i += 1


def main():
    # Inicializamos las variables compartidas entre los productores y el consumidor
    storage = [Array('i', K) for i in range(NPROD)]
    index = [Value('i', 0) for i in range(NPROD)]
    numbers = Array('i', NPROD * N)
    for j in range(NPROD):
        for i in range(K):
            storage[j][i] = -1
        print (f"almacen inicial del productor {j} es", storage[j][:], "y su índice", index[j].value)

    # Tenemos para cada productor un semáforo general, un semáforo acotado y un mutex
    # non_empty: semáforo que avisa al consumidor que hay un elemento disponible
    # empty: semáforo de tamaño K que avisa al productor de que ya puede almacenar un nuevo elemento
    # mutex: protege las variables compartidas: storage e index
    
    non_empty = [Semaphore(0) for i in range(NPROD)]
    empty = [BoundedSemaphore(K) for i in range(NPROD)]
    mutex = [Lock() for i in range(NPROD)]

    prodlst = [Process(target=producer,
                        name=f'prod_{i}',
                        args=(storage[i], index[i], empty[i], non_empty[i], mutex[i]))
                for i in range(NPROD) ]

    conslst = [Process(target=consumer,
                        name=f"cons", 
                        args=(storage, index, empty, non_empty, mutex, numbers))]

    for p in prodlst + conslst:
        p.start()
    for p in prodlst + conslst:
        p.join()

    print("¿La lista", numbers[:], "está ordenada?:", numbers[:] == sorted(numbers[:]))

if __name__ == '__main__':
    #for i in range(1):
        main()
