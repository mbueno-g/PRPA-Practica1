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


def add_data(storage, index, data, mutex, ind):
    mutex.acquire()
    try:
        storage[index.value] = data
        delay(6)
        index.value = index.value + 1
    finally:
        mutex.release()


def get_data(storage, index, mutex, ind):
    mutex.acquire()
    try:
        data = storage[ind*K]
        index.value = index.value - 1
        delay()
        for i in range(ind*K, (ind+1)*K - 1):
            storage[i] = storage[i + 1]
        storage[index.value] = -1
    finally:
        mutex.release()


def producer(storage, index, empty, non_empty, mutex, ind):
    data = randint(0,10)
    for v in range(N):
        print (f"producer {current_process().name} produciendo")
        delay(6)
        empty.acquire()
        data += randint(0,10)
        add_data(storage, index, data, mutex, ind)
        non_empty.release()
        print (f"producer {current_process().name} almacenado {data}")
    empty.acquire()
    # 
    add_data(storage,index, -1, mutex, ind)
    non_empty.release()
    print (f"producer {current_process().name} almacenado {-1}")


def haya_productores(storage):
    for i in range(NPROD):
        if (storage[i*K] != -1):
            return True
    return False


# Coge el menor elemento de la cabeza de cada proceso
def get_min(storage, index, mutex):
    n = []
    ind = []
    for i in range(NPROD):
        if (storage[i*K] != -1):
            n.append(storage[i*K])
            ind.append(i)
    value = min(n)
    k = ind[n.index(value)]
    return k, value


def consumer(storage, index, empty, non_empty, mutex, sorted_data):
    for v in range(NPROD):
        non_empty[v].acquire()
    i = 0
    while haya_productores(storage):
        print (f"consumer {current_process().name} desalmacenando")
        ind, value = get_min(storage, index, mutex)
        get_data(storage, index[ind], mutex[ind], ind)
        sorted_data[i] = value
        empty[ind].release()
        print (f"consumer {current_process().name} consumiendo {value} del producer {ind}")
        non_empty[ind].acquire()
        delay()
        i += 1


def main():
    # Inicializamos las variables compartidas entre los productores y el consumidor
    N1 = K*NPROD
    storage = Array('i', N1)
    index = [Value('i', i*K) for i in range(NPROD)]
    numbers = Array('i', NPROD * N)
    for j in range(N1):
        storage[j] = -1
    print("El único almacen es", storage[:], "y los índices son:")
    # Tenemos para cada productor un semáforo general, un semáforo acotado y un mutex
    # non_empty: semáforo que avisa al consumidor que hay un elemento disponible
    # empty: semáforo de tamaño K que avisa al productor de que ya puede almacenar un nuevo elemento
    # mutex: protege las variables compartidas: storage e index
    
    non_empty = [Semaphore(0) for i in range(NPROD)]
    empty = [BoundedSemaphore(K) for i in range(NPROD)]
    mutex = [Lock() for i in range(NPROD)]

    prodlst = [Process(target=producer,
                        name=f'prod_{i}',
                        args=(storage, index[i], empty[i], non_empty[i], mutex[i], i))
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
    main()
