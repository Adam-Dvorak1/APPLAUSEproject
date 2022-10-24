import time
from multiprocessing import Pool
import multiprocessing

__spec__ = "ModuleSpec(name='builtins', loader=<class'_frozen_importlib.BuiltinImporter'>)"  




def f(x):
    return x*x


if __name__ == "__main__":
    print("this is a test") 
    with Pool(processes=4) as pool:      
        
  # start 4 worker processes
        result = pool.apply_async(f, (10,)) # evaluate "f(10)" asynchronously in a single process
        print(result.get(timeout=1))        # prints "100" unless your computer is *very* slow

        print(pool.map(f, range(10)))       # prints "[0, 1, 4,..., 81]"

        it = pool.imap(f, range(10))
        print(next(it))                     # prints "0"
        print(next(it))
        result = pool.apply_async(time.sleep, (10,))
        print(result.get())
        print(next(it))
        print(next(it))  
        print(next(it))                     # prints "0"
        print(next(it))
        print(next(it))
        print(next(it))
    print("this is also a test")
                                # prints "1"
    #        # prints "4" unless your computer is *very* slow

#         result = pool.apply_async(time.sleep, (10,))

# bar
# def bar():
#     for i in range(100):
#         print ("Tick")
#         time.sleep(1)

# if __name__ == '__main__':
#     # Start bar as a process
#     p = multiprocessing.Process(target=bar)
#     p.start()

#     # Wait for 10 seconds or until process finishes
#     p.join(10)

#     # If thread is still active
#     if p.is_alive():
#         print ("running... let's kill it...")

#         # Terminate - may not work if process is stuck for good
#         p.terminate()
#         # OR Kill - will work for sure, no chance for process to finish nicely however
#         # p.kill()

#         p.join()