#!/usr/bin/env python
# Test of MPI module 'pypar' for Python
# 
# Run as 
#   python testpypar.py
# or 
#   mpirun -np 2 testpypar.py
# (perhaps try number of processors more than 2)
#
# To verify bandwidth of your architecture please run pytiming (and ctiming) 
#
# OMN, GPC FEB 2002


try:
  import numpy
except:
  raise 'Module numpy must be present to run pypar'


#print "Importing pypar"
import pypar
methods = dir(pypar)
assert 'abort' in methods
assert 'finalize' in methods
assert 'get_processor_name' in methods
assert 'time' in methods
assert 'rank' in methods
assert 'receive' in methods
assert 'send' in methods
assert 'broadcast' in methods
assert 'size' in methods

#print "Module pypar imported OK"
#pypar.Barrier()



# Shorthands as tests were written prior to version 2.0
# Eventually, modify all tests to use buffers and remove
# the 'raw' form.
def raw_send(x, destination, tag=pypar.default_tag, vanilla=0):
    pypar.send(x, destination, use_buffer=True, tag=tag, vanilla=vanilla) 

def raw_receive(x, source, tag=pypar.default_tag, vanilla=0, return_status=0):
    x = pypar.receive(source, tag=tag, vanilla=vanilla,
                      return_status=return_status, buffer=x)
    return x

def raw_scatter(x, buffer, source, vanilla=0):
    pypar.scatter(x, source, buffer=buffer, vanilla=vanilla)


def raw_gather(x, buffer, source, vanilla=0):
    pypar.gather(x, source, buffer=buffer, vanilla=0)  

def raw_reduce(x, buffer, op, source, vanilla=0):
    pypar.reduce(x, op, source, buffer=buffer, vanilla=0)













myid =    pypar.rank()
numproc = pypar.size()
node =    pypar.get_processor_name()

print 'I am processor %d of %d on node %s' %(myid, numproc, node)
pypar.barrier()


if numproc > 1:
  # Test simple raw communication (arrays, strings and general)
  #
  N = 17 #Number of elements
  
  if myid == 0:
    # Integer arrays
    #
    A = numpy.array(range(N)).astype('i')
    B = numpy.zeros(N).astype('i')
    raw_send(A,1)
    raw_receive(B,numproc-1)

    assert numpy.allclose(A, B)
    print 'Raw communication of numeric integer arrays OK'


    # Long integer arrays
    #
    A = numpy.array(range(N)).astype('l')
    B = numpy.zeros(N).astype('l')    
    raw_send(A,1)
    raw_receive(B,numproc-1)
    
    assert numpy.allclose(A, B)
    print "Raw communication of numeric long integer arrays OK"

    # Real arrays
    #
    A = numpy.array(range(N)).astype('f')
    B = numpy.zeros(N).astype('f')    
    raw_send(A,1)
    raw_receive(B,numproc-1)
    
    assert numpy.allclose(A, B)    
    print "Raw communication of numeric real arrays OK"

    # Complex arrays
    #
    A = numpy.array(range(N)).astype('D')
    A += 3j
    B = numpy.zeros(N).astype('D')
    raw_send(A, 1)
    B = raw_receive(B, numproc-1)

    assert numpy.allclose(A, B)    
    print "Raw communication of numeric complex arrays OK"

    # Strings (< 256 characters)
    #
    A = "and now to something completely different !"
    B = " "*len(A)
    raw_send(A,1)
    B, status = raw_receive(B,numproc-1,return_status=True)

    assert A == B
    print "Raw communication of strings OK"
    
    # A more general structure
    #
    A = ['ABC', (1,2,3.14), {8: 'Monty'}, numpy.array([13.45, 1.2])]
    B = ['   ', (0,0,0.0) , {0: '     '}, numpy.zeros(2).astype('f')]    
    raw_send(A,1)
    B, status = raw_receive(B,numproc-1, return_status=True)

    OK = True
    for i, a in enumerate(A):
      b = B[i]

      if type(a).__name__ == 'ndarray':
        if not numpy.allclose(a, b):
          OK = False
          break
      elif a != b:
        OK = False
        break

    if OK is True:
      print 'Raw communication of general structures OK' 
    else:
      raise Exception    

    
  else:  
    # Integers
    #
    X = numpy.zeros(N).astype('i')    
    raw_receive(X, myid-1)  
    raw_send(X, (myid+1)%numproc)
  
    # Long integers
    #
    X = numpy.zeros(N).astype('l')
    raw_receive(X, myid-1)  
    raw_send(X, (myid+1)%numproc)    

    # Floats
    #
    X = numpy.zeros(N).astype('f')
    raw_receive(X, myid-1)  
    raw_send(X, (myid+1)%numproc)    

    # Complex
    #
    X = numpy.zeros(N).astype('D')
    X = raw_receive(X, myid-1)  
    raw_send(X, (myid+1)%numproc)    

    # Strings
    #
    X = " "*256
    raw_receive(X, myid-1)  
    raw_send(X.strip(), (myid+1)%numproc)    

    # General
    #
    X = ['   ', (0,0,0.0), {0: '     '}, numpy.zeros(2).astype('f')]
    X = raw_receive(X, myid-1)  
    raw_send(X, (myid+1)%numproc)    
    




  #Test (raw communication of) multi dimensional arrays

  M = 13  #Number of elements in dim 1
  N = 17  #Number of elements in higher dims
  
  if myid == 0:
    # 2D real arrays
    #
    A = numpy.array(range(M*N)).astype('f')
    B = numpy.zeros(M*N).astype('f')

    A = numpy.reshape(A, (M,N))
    B = numpy.reshape(B, (M,N))    
    
    raw_send(A,1)
    raw_receive(B,numproc-1)
    
    assert numpy.allclose(A, B)    
    print "Raw communication of 2D real arrays OK"

    # 2D complex arrays
    #
    A = numpy.array(range(M*N)).astype('D')
    B = numpy.zeros(M*N).astype('D')

    A = numpy.reshape(A, (M,N))
    B = numpy.reshape(B, (M,N))    

    raw_send(A,1)
    raw_receive(B,numproc-1)
    
    assert numpy.allclose(A, B)    
    print "Raw communication of 2D complex arrays OK"

    # 3D real arrays
    #
    A = numpy.array(range(M*N*N)).astype('f')
    B = numpy.zeros(M*N*N).astype('f')

    A = numpy.reshape(A, (M,N,N))
    B = numpy.reshape(B, (M,N,N))    
    
    raw_send(A,1)
    raw_receive(B,numproc-1)
    
    assert numpy.allclose(A, B)    
    print "Raw communication of 3D real real arrays OK"

    # 4D real arrays
    #
    A = numpy.array(range(M*N*N*M)).astype('f')
    B = numpy.zeros(M*N*N*M).astype('f')

    A = numpy.reshape(A, (M,N,N,M))
    B = numpy.reshape(B, (M,N,N,M))    
    
    raw_send(A,1)
    raw_receive(B,numproc-1)
    
    assert numpy.allclose(A, B)    
    print "Raw communication of 4D real real arrays OK"

    # 5D real arrays
    #
    A = numpy.array(range(M*N*2*N*M)).astype('f')
    B = numpy.zeros(M*N*2*N*M).astype('f')

    A = numpy.reshape(A, (M,N,2,N,M))
    B = numpy.reshape(B, (M,N,2,N,M))    
    
    raw_send(A,1)
    raw_receive(B,numproc-1)
    
    assert numpy.allclose(A, B)    
    print "Raw communication of 5D real real arrays OK"

    # 5D double arrays
    #
    A = numpy.array(range(M*N*2*N*M)).astype('d')
    B = numpy.zeros(M*N*2*N*M).astype('d')

    A = numpy.reshape(A, (M,N,2,N,M))
    B = numpy.reshape(B, (M,N,2,N,M))    
    
    raw_send(A,1)
    raw_receive(B,numproc-1)
    
    assert numpy.allclose(A, B)    
    print "Raw communication of 5D double arrays OK"

    # 5D complex arrays
    #
    A = numpy.array(range(M*N*2*N*M)).astype('D')
    B = numpy.zeros(M*N*2*N*M).astype('D')

    A = numpy.reshape(A, (M,N,2,N,M))
    B = numpy.reshape(B, (M,N,2,N,M))    
    
    raw_send(A,1)
    raw_receive(B,numproc-1)
    
    assert numpy.allclose(A, B)    
    print "Raw communication of 5D complex arrays OK"
  else:  
    # 2D real arrays
    #
    X = numpy.zeros(M*N).astype('f')
    X = numpy.reshape(X, (M,N))
    
    raw_receive(X, myid-1)  
    raw_send(X, (myid+1)%numproc)
  
    # 2D complex arrays
    #
    X = numpy.zeros(M*N).astype('D')
    X = numpy.reshape(X, (M,N))

    X = raw_receive(X, myid-1)
    raw_send(X, (myid+1)%numproc)
  
    # 3D real arrays
    #
    X = numpy.zeros(M*N*N).astype('f')
    X = numpy.reshape(X, (M,N,N))
    
    raw_receive(X, myid-1)  
    raw_send(X, (myid+1)%numproc)

    # 4D real arrays
    #
    X = numpy.zeros(M*N*N*M).astype('f')
    X = numpy.reshape(X, (M,N,N,M))
    
    raw_receive(X, myid-1)  
    raw_send(X, (myid+1)%numproc)

    # 5D real arrays
    #
    X = numpy.zeros(M*N*2*N*M).astype('f')
    X = numpy.reshape(X, (M,N,2,N,M))
    
    raw_receive(X, myid-1)  
    raw_send(X, (myid+1)%numproc)

    # 5D double arrays
    #
    X = numpy.zeros(M*N*2*N*M).astype('d')
    X = numpy.reshape(X, (M,N,2,N,M))
    
    raw_receive(X, myid-1)  
    raw_send(X, (myid+1)%numproc)

    # 5D complex arrays
    #
    X = numpy.zeros(M*N*2*N*M).astype('D')
    X = numpy.reshape(X, (M,N,2,N,M))
    
    raw_receive(X, myid-1)  
    raw_send(X, (myid+1)%numproc)

  # Test easy communication  - without buffers (arrays, strings and general)
  #
  N = 17 #Number of elements
  
  if myid == 0:
    # Integer arrays
    #
    A = numpy.array(range(N))

    pypar.send(A,1)
    B = pypar.receive(numproc-1)
    

    assert numpy.allclose(A, B)
    print "Simplified communication of numeric integer arrays OK"

    # Long integer arrays
    #
    A = numpy.array(range(N)).astype('l')
    pypar.send(A,1)
    B=pypar.receive(numproc-1)
    
    assert numpy.allclose(A, B)    
    print "Simplified communication of long integer real arrays OK"

    # Real arrays
    #
    A = numpy.array(range(N)).astype('f')
    pypar.send(A,1)
    B=pypar.receive(numproc-1)
    
    assert numpy.allclose(A, B)    
    print "Simplified communication of numeric real arrays OK"

    # Complex arrays
    #
    A = numpy.array(range(N)).astype('D')
    A += 3j
    pypar.send(A,1)
    B=pypar.receive(numproc-1)

    assert numpy.allclose(A, B)    
    print "Simplified communication of numeric complex arrays OK"


    # Strings
    #
    A = "and now to something completely different !"
    pypar.send(A,1)
    B=pypar.receive(numproc-1)
    
    assert A == B
    print "Simplified communication of strings OK"
    
    # A more general structure
    #
    A = ['ABC', (1,2,3.14), {8: 'Monty'}, numpy.array([13.45, 1.2])]
    pypar.send(A,1)
    B = pypar.receive(numproc-1)

    OK = True
    for i, a in enumerate(A):
      b = B[i]

      if type(a).__name__ == 'ndarray':
        if not numpy.allclose(a, b):
          OK = False
          break
      elif a != b:
        OK = False
        break

    if OK is True:
      print 'Simplified communication of general structures OK' 
    else:
      raise Exception    
    
  else:  
    # Integers
    #
    X=pypar.receive(myid-1)  
    pypar.send(X, (myid+1)%numproc)
  
    # Long integers
    #
    X=pypar.receive(myid-1)  
    pypar.send(X, (myid+1)%numproc)    

    # Floats
    #
    X=pypar.receive(myid-1)  
    pypar.send(X, (myid+1)%numproc)    

    # Complex
    #
    X=pypar.receive(myid-1)  
    pypar.send(X, (myid+1)%numproc)    

    # Strings
    #
    X=pypar.receive(myid-1)  
    pypar.send(X, (myid+1)%numproc)    

    # General
    #
    X = pypar.receive(myid-1)  
    pypar.send(X, (myid+1)%numproc)    




    
  #Test (easy communication of) multi dimensional arrays

  M = 13  #Number of elements in dim 1
  N = 17  #Number of elements in higher dims
  
  if myid == 0:
    # 2D real arrays
    #
    A = numpy.array(range(M*N)).astype('f')

    A = numpy.reshape(A, (M,N))
    
    pypar.send(A,1)
    B = pypar.receive(numproc-1)
    
    assert numpy.allclose(A, B)    
    print "Simplified communication of 2D real arrays OK"

    # 3D real arrays
    #
    A = numpy.array(range(M*N*N)).astype('f')
    A = numpy.reshape(A, (M,N,N))
    
    pypar.send(A,1)
    B=pypar.receive(numproc-1)
    
    assert numpy.allclose(A, B)    
    print "Simplified communication of 3D real arrays OK"

    # 4D real arrays
    #
    A = numpy.array(range(M*N*N*M)).astype('f')
    A = numpy.reshape(A, (M,N,N,M))
    
    pypar.send(A,1)
    B=pypar.receive(numproc-1)
    
    assert numpy.allclose(A, B)    
    print "Simplified communication of 4D real arrays OK"

    # 5D real arrays
    #
    A = numpy.array(range(M*N*2*N*M)).astype('f')
    A = numpy.reshape(A, (M,N,2,N,M))
    
    pypar.send(A,1)
    B=pypar.receive(numproc-1)
    
    assert numpy.allclose(A, B)    
    print "Simplified communication of 5D real arrays OK"

    # 5D double arrays
    #
    A = numpy.array(range(M*N*2*N*M)).astype('d')
    A = numpy.reshape(A, (M,N,2,N,M))
    
    pypar.send(A,1)
    B=pypar.receive(numproc-1)
    
    assert numpy.allclose(A, B)    
    print "Simplified communication of 5D double arrays OK"

    # 5D complex arrays
    #
    A = numpy.array(range(M*N*2*N*M)).astype('D')
    A = numpy.reshape(A, (M,N,2,N,M))
    
    pypar.send(A,1)
    B=pypar.receive(numproc-1)
    
    assert numpy.allclose(A, B)    
    print "Simplified communication of 5D complex real arrays OK"

  else:  
    # 2D real arrays
    #
    
    X = pypar.receive(myid-1)  
    pypar.send(X, (myid+1)%numproc)
  
    # 3D real arrays
    #
    X=pypar.receive(myid-1)  
    pypar.send(X, (myid+1)%numproc)

    # 4D real arrays
    #
    X = pypar.receive(myid-1)  
    pypar.send(X, (myid+1)%numproc)

    # 5D real arrays
    #
    X=pypar.receive(myid-1)  
    pypar.send(X, (myid+1)%numproc)

    # 5D double arrays
    #
    X=pypar.receive(myid-1)  
    pypar.send(X, (myid+1)%numproc)

    # 5D complex arrays
    #
    X=pypar.receive(myid-1)  
    pypar.send(X, (myid+1)%numproc)

  # Test broadcast  - with buffers (arrays, strings and general)
  #
      
  testString = ('test' + str(myid)).ljust(10)  #Buffers must have the same length on all procs!
  pypar.broadcast(testString, 0)
  assert testString.strip() == 'test0'
  
  testString = ('test' + str(myid)).ljust(10)  #Buffers must have the same length on all procs!
  pypar.broadcast(testString, numproc-1)
  assert testString.strip() == 'test' + str(numproc-1)
  
  if myid == 0:
    print "Broadcast communication of strings OK"

  ####################################################  
  N = 17 #Number of elements
  testArray = myid * numpy.array(range(N))
  pypar.broadcast(testArray, 1)
  assert numpy.allclose(testArray, 1 * testArray)
  
  if myid == 0:    
    print "Broadcast communication of numeric integer array OK"


  testArray = myid * numpy.array(range(N)).astype('f')
  pypar.broadcast(testArray, 1)
  assert numpy.allclose(testArray, 1 * testArray)
  if myid == 0:
    print "Broadcast communication of numeric real array OK"


  M = 13
  testArray = myid * numpy.array(range(M*N)).astype('f')
  testArray = numpy.reshape(testArray, (M,N))  
  pypar.broadcast(testArray, 1)
  assert numpy.allclose(testArray, 1 * testArray)
  if myid == 0:
    print "Broadcast communication of 2D numeric real array OK"

  testArray = myid * numpy.array(range(M*2*N)).astype('f')
  testArray = numpy.reshape(testArray, (M,2,N))  
  pypar.broadcast(testArray, 1)
  assert numpy.allclose(testArray, 1 * testArray)
  if myid == 0:
    print "Broadcast communication of 3D numeric real array OK"

  testArray = myid * numpy.array(range(M*2*N)).astype('D')
  testArray = numpy.reshape(testArray, (M,2,N))  
  pypar.broadcast(testArray, 1)
  assert numpy.allclose(testArray, 1 * testArray)
  if myid == 0:
    print "Broadcast communication of 3D numeric complex array OK"

    
  A_x = ['ABC', myid, (1,2,3), {8: 'Monty'}, numpy.array([13.45, 1.2])]
  A_1 = ['ABC',    1, (1,2,3), {8: 'Monty'}, numpy.array([13.45, 1.2])]
  B = pypar.broadcast(A_x, 1)

  OK = True
  for i, a in enumerate(A_1):
    b = B[i]

    if type(a).__name__ == 'ndarray':
      if not numpy.allclose(a, b):
        OK = False
        break
    elif a != b:
      OK = False
      break

  if OK is False:
    raise Exception    
    
  if myid == 0:
    print "Broadcast communication of general structures OK"
  



  # Test scatter  - with/without buffers (arrays, strings)
  #
  N = 16 #Number of elements

  NP = N/numproc
  
  testString = 'ABCDEFGHIJKLMNOP'  #Length = 16
  X = ' '*NP

  #print 'P%d: s=%s, r=%s' %(myid, testString, X)
  #raw_scatter(testString, X, 2)
  #Y = pypar.scatter(testString, 2)


  #assert X==Y, 'X=%s, Y=%s' %(X,Y)
  #assert Y == testString[myid*NP:(myid+1)*NP]
  #assert X == testString[myid*NP:(myid+1)*NP]

  #if myid == 0:    
  #  print "Scatter communication of strings OK"
    

  #Scatter Arrays
  testArray = numpy.array(range(N)).astype('i')
  X = numpy.zeros(NP).astype('i')
  raw_scatter(testArray, X, 0)
  Y = pypar.scatter(testArray, 0)

  assert numpy.allclose(X, Y)  
  assert numpy.allclose(X, testArray[myid*NP:(myid+1)*NP])
  assert numpy.allclose(Y, testArray[myid*NP:(myid+1)*NP])   

  if myid == 0:
    print "Scatter communication of numeric integer array OK"


  testArray = numpy.array(range(N)).astype('f')
  X = numpy.zeros(NP).astype('f')
  raw_scatter(testArray, X, 0)
    
  Y = pypar.scatter(testArray, 0)

  assert numpy.allclose(X, Y)  
  assert numpy.allclose(X, testArray[myid*NP:(myid+1)*NP])
  assert numpy.allclose(Y, testArray[myid*NP:(myid+1)*NP])   

  if myid == 0:
    print "Scatter communication of numeric real arrays OK"
  #else:
  #  print X, testArray, Y
  #  assert numpy.allclose(X, Y)

  testArray = numpy.array(range(N)).astype('D')
  X = numpy.zeros(NP).astype('D')
  raw_scatter(testArray, X, 0)
    
  Y = pypar.scatter(testArray, 0)

  assert numpy.allclose(X, Y)  
  assert numpy.allclose(X, testArray[myid*NP:(myid+1)*NP])
  assert numpy.allclose(Y, testArray[myid*NP:(myid+1)*NP])   

  if myid == 0:
    print "Scatter communication of numeric complex array OK"


###################################################
#FIXME: 2D scatter doesn't work yet    
#   M = 16
#   N = 13
#   MP = M/numproc
  
#   testArray = numpy.array(range(M*N)).astype('D')
#   testArray = numpy.reshape(testArray, (M,N))    
#   X = numpy.zeros(MP*N).astype('D')
#   X = numpy.reshape(X, (MP,N))
  
#   raw_scatter(testArray, X, 0)
#   Y = pypar.scatter(testArray, 0)
  
#   assert numpy.allclose(X, Y)  
#   assert numpy.allclose(X, testArray[myid*MP:(myid+1)*MP,:])
#   assert numpy.allclose(Y, testArray[myid*MP:(myid+1)*MP,:])   

#   if myid == 0:
#     print "Scatter communication of 2D numeric complex array OK"



  # Test gather  - with/without buffers (arrays, strings)
  #
  N = 17 #Number of elements
      
  testString = 'AB'
  X = '_'*(len(testString)*numproc)    #Blanks caused errors when numproc >= 6 
  raw_gather(testString, X, 0)

  Y =  pypar.gather(testString, 0) 
  
  if myid == 0:
    assert X == 'AB' * numproc
    assert Y == 'AB' * numproc
    print "Gather communication of strings OK"
  

  testArray = numpy.array(range(N)).astype('i')
  X = numpy.zeros(N*numproc).astype('i')
  raw_gather(testArray, X, 0)

  Y = pypar.gather(testArray, 0)
  
  if myid == 0:
    for i in range(numproc):       
      assert numpy.allclose(testArray, X[(i * N): ((i+1)*N)])

    assert numpy.allclose(X, Y)
    print "Gather communication of numeric integer array OK"
    
    
  testArray = numpy.array(range(N)).astype('f')
  X = numpy.zeros(N*numproc).astype('f')
  raw_gather(testArray, X, 0)
  
  Y = pypar.gather(testArray, 0)
  if myid == 0:
    for i in range(numproc):       
      assert numpy.allclose(testArray, X[(i * N): ((i+1)*N)])
    assert numpy.allclose(X, Y)      
    print "Gather communication of numeric real array OK"
    
  
  testArray = numpy.array(range(N)).astype('D')
  X = numpy.zeros(N*numproc).astype('D')
  raw_gather(testArray, X, 0)
  
  Y = pypar.gather(testArray, 0)
  if myid == 0:
    for i in range(numproc):       
      assert numpy.allclose(testArray, X[(i * N): ((i+1)*N)])
    assert numpy.allclose(X, Y)      
    print "Gather communication of numeric complex arrays OK"

  M = 13  
  testArray = numpy.array(range(M*N)).astype('D')
  testArray = numpy.reshape(testArray, (M,N))
  X = numpy.zeros(M*N*numproc).astype('D')
  X = numpy.reshape(X, (M*numproc,N))
  
  raw_gather(testArray, X, 0)
  
  Y = pypar.gather(testArray, 0)
  if myid == 0:
    for i in range(numproc):       
      assert numpy.allclose(testArray, X[(i * M): ((i+1)*M), :])
    assert numpy.allclose(X, Y)      
    print "Gather communication of 2D numeric complex arrays OK"
    
  
  ########################################################
  # Test reduce
  #######################################################
  N = 17 #Number of elements
  
  # Create one (different) array on each processor
  #    
  testArray = numpy.array(range(N)).astype('i') * (myid+1)
  #print testArray
  X = numpy.zeros(N).astype('i') # Buffer for results

  raw_reduce(testArray, X, pypar.SUM, 0)
  if myid == 0:
    Y = numpy.zeros(N).astype('i')
    for i in range(numproc):
      Y = Y+numpy.array(range(N)).astype('i')*(i+1)    
    #print X
    #print Y  
    assert numpy.allclose(X, Y)
    print "Raw reduce using pypar.SUM OK"
        
  raw_reduce(testArray, X, pypar.MAX, 0, 0)
  if myid == 0:
    Y = numpy.array(range(N))*numproc
    assert numpy.allclose(X, Y)
    print "Raw reduce using pypar.MAX OK"

  raw_reduce(testArray, X, pypar.MIN, 0, 0)
  if myid == 0:
    Y = numpy.array(range(N))
    assert numpy.allclose(X, Y)
    print "Raw reduce using pypar.MIN OK"
    
  if numproc <= 20:
    testArray_float = testArray.astype('f')  #Make room for big results
    X_float = X.astype('f')
    raw_reduce(testArray_float, X_float, pypar.PROD, 0, 0)
    if myid == 0:
      Y = numpy.ones(N).astype('f')    
      for i in range(numproc):
        Y = Y*numpy.array(range(N))*(i+1)    
      #print X_float
      #print Y  
      assert numpy.allclose(X_float, Y)
      print "Raw reduce using pypar.PROD OK"
  else:
    if myid == 0:
      print "Skipping product-reduce - try again with numproc < 20"    

  raw_reduce(testArray, X, pypar.LAND, 0, 0)
  if myid == 0:  
    Y = numpy.ones(N).astype('i')    
    for i in range(numproc):
      Y = numpy.logical_and(Y, numpy.array(range(N)).astype('i')*(i+1))  
    assert numpy.allclose(X, Y)
    print "Raw reduce using pypar.LAND OK"    
    
  raw_reduce(testArray, X, pypar.BAND, 0, 0)
  if myid == 0:
    Y = numpy.ones(N).astype('i')*255  #Neutral element for &   
    for i in range(numproc):
      Y = numpy.bitwise_and(Y, numpy.array(range(N))*(i+1))
    assert numpy.allclose(X, Y)
    print "Raw reduce using pypar.BAND OK"    

  raw_reduce(testArray, X, pypar.LOR, 0, 0)
  if myid == 0:  
    Y = numpy.zeros(N).astype('i')    
    for i in range(numproc):
      Y = numpy.logical_or(Y, numpy.array(range(N)).astype('i')*(i+1))  
    assert numpy.allclose(X, Y)
    print "Raw reduce using pypar.LOR OK"    
  
  raw_reduce(testArray, X, pypar.BOR, 0, 0)
  if myid == 0:
    Y = numpy.zeros(N).astype('i')   #Neutral element for |   
    for i in range(numproc):
      Y = numpy.bitwise_or(Y, numpy.array(range(N)).astype('i')*(i+1))
    assert numpy.allclose(X, Y)
    print "Raw reduce using pypar.BOR OK"    

  raw_reduce(testArray, X, pypar.LXOR, 0, 0)
  if myid == 0:  
    Y = numpy.zeros(N).astype('i')    
    for i in range(numproc):
      Y = numpy.logical_xor(Y, numpy.array(range(N)).astype('i')*(i+1))  
    assert numpy.allclose(X, Y)
    print "Raw reduce using pypar.LXOR OK"    

  raw_reduce(testArray, X, pypar.BXOR, 0, 0)
  if myid == 0:
    Y = numpy.zeros(N).astype('i')   #Neutral element for xor ?   
    for i in range(numproc):
      Y = numpy.bitwise_xor(Y, numpy.array(range(N)).astype('i')*(i+1))
    assert numpy.allclose(X, Y)
    print "Raw reduce using pypar.BXOR OK"    

  # NOT YET SUPPORTED
  #  
  #raw_reduce(testArray, X, N, pypar.MAXLOC, 0, 0)  
  #if myid == 0:
  #  print 'MAXLOC', X
  #raw_reduce(testArray, X, N, pypar.MINLOC, 0, 0)
  #if myid == 0:
  #  print 'MINLOC', X
  
  #
  #  FIXME
  # Don't know how to test this (not available on all MPI systems)
  #
  #raw_reduce(testArray, X, N, pypar.REPLACE, 0, 0)
  #if myid == 0:
  #  print 'REPLACE', X



  # Test status block (simple communication)
  N = 17  
  if myid == 0:
    # Integer arrays
    #
    A = numpy.array(range(N)).astype('i')

    pypar.send(A,1)
    B, status = pypar.receive(numproc-1, return_status = True)

    repr(status)  # Check that status can be printed

    sz = A.itemsize
    assert numpy.allclose(A, B)
    assert len(B) == status.length, 'Reported length == %d should be %d'\
           %(status.length, len(B))
    assert status.size == sz, 'Reported size == %d should be %d'\
           %(status.size, sz)
    assert status.tag == pypar.default_tag, 'Reported tag == %d should be %d'\
           %(status.tag, pypar.default_tag)
    assert status.error == 0
    assert status.source == numproc-1, 'Reported source == %d should be %d'\
           %(status.source, numproc-1)

    print "Status object (numeric integer arrays) OK"
           
    # Real arrays
    #
    A = numpy.array(range(N)).astype('f')
    pypar.send(A,1)
    B, status = pypar.receive(numproc-1, return_status = True)    

    sz = A.itemsize    
    assert numpy.allclose(A, B)
    assert len(B) == status.length, 'Reported length == %d should be %d'\
           %(status.length, len(B))
    assert status.size == sz, 'Reported size == %d should be %d'\
           %(status.size, sz)
    assert status.tag == pypar.default_tag, 'Reported tag == %d should be %d'\
           %(status.tag, pypar.default_tag)
    assert status.error == 0
    assert status.source == numproc-1, 'Reported source == %d should be %d'\
           %(status.source, numproc-1)
    
    print "Status object (numeric real arrays) OK"

    # Strings
    #
    A = "and now to something completely different !"
    pypar.send(A,1)
    B, status = pypar.receive(numproc-1, return_status = True)        

    sz = 1 #Characters are one byte long
    assert A == B
    assert len(B) == status.length, 'Reported length == %d should be %d'\
           %(status.length, len(B))
    assert status.size == sz, 'Reported size == %d should be %d'\
           %(status.size, sz)
    assert status.tag == pypar.default_tag, 'Reported tag == %d should be %d'\
           %(status.tag, pypar.default_tag)
    assert status.error == 0
    assert status.source == numproc-1, 'Reported source == %d should be %d'\
           %(status.source, numproc-1)
    
    print "Status object (strings) OK"
    
    # A more general structure
    #
    A = ['ABC', (1,2,3.14), {8: 'Monty'}, numpy.array([13.45, 1.2])]
    pypar.send(A,1)
    B, status = pypar.receive(numproc-1, return_status = True)            

    OK = True
    for i, a in enumerate(A):
      b = B[i]

      if type(a).__name__ == 'ndarray':
        if not numpy.allclose(a, b):
          OK = False
          break
      elif a != b:
        OK = False
        break

    if OK is True:
      print 'Status object (more general structures) OK' 
    else:
      raise Exception    
    

    #Length is the number of characters needed to encode the structure
    #Can't think of a test.

    sz = 1
    assert status.size == sz, 'Reported size == %d should be %d'\
           %(status.size, sz)
    assert status.tag == pypar.default_tag, 'Reported tag == %d should be %d'\
           %(status.tag, pypar.default_tag)
    assert status.error == 0
    assert status.source == numproc-1, 'Reported source == %d should be %d'\
           %(status.source, numproc-1)

    print "Status object (general structures) OK"
    
  else:  
    # Integers
    #
    X=pypar.receive(myid-1)  
    pypar.send(X, (myid+1)%numproc)
  
    # Floats
    #
    X=pypar.receive(myid-1)  
    pypar.send(X, (myid+1)%numproc)    

    # Strings
    #
    X=pypar.receive(myid-1)  
    pypar.send(X, (myid+1)%numproc)    

    # General
    #
    X = pypar.receive(myid-1)  
    pypar.send(X, (myid+1)%numproc)    








  # Test status block (raw communication)
  N = 17 #Number of elements
  if myid == 0:
    # Integer arrays
    #
    A = numpy.array(range(N)).astype('i')
    B = numpy.zeros(N).astype('i')    
    raw_send(A,1)
    B, status = raw_receive(B,numproc-1,return_status=True)
    
    assert numpy.allclose(A, B)

    sz = A.itemsize
    assert numpy.allclose(A, B)
    assert len(B) == status.length, 'Reported length == %d should be %d'\
           %(status.length, len(B))
    assert status.size == sz, 'Reported size == %d should be %d'\
           %(status.size, sz)
    assert status.tag == pypar.default_tag, 'Reported tag == %d should be %d'\
           %(status.tag, pypar.default_tag)
    assert status.error == 0
    assert status.source == numproc-1, 'Reported source == %d should be %d'\
           %(status.source, numproc-1)

    print "Status object (raw numeric integer arrays) OK"


    # Real arrays
    #
    A = numpy.array(range(N)).astype('f')
    B = numpy.zeros(N).astype('f')    
    raw_send(A,1)
    B, status = raw_receive(B,numproc-1,return_status=True)    
    
    assert numpy.allclose(A, B)
    sz = A.itemsize
    assert numpy.allclose(A, B)
    assert len(B) == status.length, 'Reported length == %d should be %d'\
           %(status.length, len(B))
    assert status.size == sz, 'Reported size == %d should be %d'\
           %(status.size, sz)
    assert status.tag == pypar.default_tag, 'Reported tag == %d should be %d'\
           %(status.tag, pypar.default_tag)
    assert status.error == 0
    assert status.source == numproc-1, 'Reported source == %d should be %d'\
           %(status.source, numproc-1)

    print "Status object (raw numeric real arrays) OK"

    # Strings (< 256 characters)
    #
    A = "and now to something completely different !"
    B = " "*len(A)
    raw_send(A,1)
    B, status = raw_receive(B,numproc-1,return_status=True)


    sz = 1 #Characters are one byte long
    assert A == B
    assert len(B) == status.length, 'Reported length == %d should be %d'\
           %(status.length, len(B))
    assert status.size == sz, 'Reported size == %d should be %d'\
           %(status.size, sz)
    assert status.tag == pypar.default_tag, 'Reported tag == %d should be %d'\
           %(status.tag, pypar.default_tag)
    assert status.error == 0
    assert status.source == numproc-1, 'Reported source == %d should be %d'\
           %(status.source, numproc-1)

    print "Status object (raw strings) OK"
    

    
    # A more general structure
    #
    A = ['ABC', (1,2,3.14), {8: 'Monty'}, numpy.array([13.45, 1.2])]
    B = ['   ', (0,0,0.0), {0: '     '}, numpy.zeros(2).astype('f')]    
    raw_send(A,1)
    B, status = raw_receive(B,numproc-1, return_status=True)


    #assert A == B
    sz = 1
    assert status.size == sz, 'Reported size == %d should be %d'\
           %(status.size, sz)
    assert status.tag == pypar.default_tag, 'Reported tag == %d should be %d'\
           %(status.tag, pypar.default_tag)
    assert status.error == 0
    assert status.source == numproc-1, 'Reported source == %d should be %d'\
           %(status.source, numproc-1)

    
    print "Status object (raw general structures) OK"
    
   
  else:  
    # Integers
    #
    X = numpy.zeros(N).astype('i')    
    raw_receive(X, myid-1)  
    raw_send(X, (myid+1)%numproc)
  
    # Floats
    #
    X = numpy.zeros(N).astype('f')
    raw_receive(X, myid-1)  
    raw_send(X, (myid+1)%numproc)    

    
    # Strings
    #
    X = " "*256
    X = raw_receive(X, myid-1)  
    raw_send(X.strip(), (myid+1)%numproc)    

    # General
    #
    X = ['   ', (0,0,0.0), {0: '     '}, numpy.zeros(2).astype('f')]
    X = raw_receive(X, myid-1)  
    raw_send(X, (myid+1)%numproc)    
    


pypar.finalize()




