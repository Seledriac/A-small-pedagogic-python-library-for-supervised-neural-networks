
# -*- coding:utf-8 -*-


"""
This module contains a class which models a feedforward neural network
"""

#Third-party libraries
import tkinter as tk
import numpy as np
import random
from matplotlib import pyplot as plt
plt.ion() #for interactive plotting
from PIL import Image
import matplotlib.image as mpimg
from math import sqrt, ceil
import warnings
np.seterr(all='warn')

class Network():

    """The Network class, modeling a feedforward neural network, trainable with standard SGD/backpropagation algorithm method"""

    def __init__(self, id, sizes, activation_function_name = 'sigmoid', regu_name = None):
        """
        Network instance constructor. It assigns six descriptives attributes : 
            - Two attributes modeling the shape of the network :
                - "sizes", a list containing the size of each layer of the network in order, with the first number and last number being the shapes of the input and output layers respectively
                - "num_layers", the total number of layers,
            - Two attributes giving the characteristics of each layer (randomly initialized)
                - "biases", A list of column matrixes, each column representing the biases of each neuron for each layer
                - "weights", A list of 2D-matrixes, each containing the weights of the synapses leading to each neuron in a given layer (one neuron = one matrix line, one synapse = one matrix column)
            - The activation function name (a non-linear function applying to each layer's output): by default, sigmoid
            - The network's output regulation method (a non-linear function applying to the model's last layer's output) : by default, None
        And an identifier "id"
        For instance, to create a Network with an input layer of 784 neurons, a hidden layer of 15 neurons, and an output layer of 10 neurons (sigmoid activation, no regulation), you should do : "net = Network("net", [784,15,10])"
        """
        #The shape of the network is saved in theese two attributes 
        self.sizes = sizes
        self.num_layers = len(sizes)
        #Creates one bias column matrix for each layer appart from the input one
        self.biases = [np.random.randn(x, 1) for x in sizes[1:]]
        #Creates one 2D-matrix for each layer appart from the input one
        #Note : The weights matrixes linking the n-th layer of size x to the (n+1)th layer of size y are matrixes of size y,x : this makes the W.A + B matrix computation straightforward (where W is the weights matrix, A the input activations matrix, and B the biases matrix)
        self.weights = [np.random.randn(y, x) for x,y in zip(sizes[:-1], sizes[1:])]
        self.id = str(id)
        self.activation_function_name = activation_function_name
        self.regu_name = regu_name
        
    def feedforward(self, a):
        """This method returns the output of the network, given : the input a in parameter (in a matrix column form), the weights and biases of the model, the activation/regulation functions, and the network's output shape"""
        for w,b in zip(self.weights, self.biases):
            #A' = activation_function(W.A+B)
            a = self.regu(self.activation_function(np.dot(w, a) + b))
        return a

    def SGD(self, training_data, epochs, mini_batch_size, eta = 3, min_eta = 1.5, test_data = None, flags_per_epoch = 5, Verbose=True, dropout_value = None, optimize_accuracy=False):
        """
        The Stochastic Gradient Descent training method, trains the network to make it fit the training data, with a number of epochs specified, with flags per epoch, mini-batch size, a dropout percentage, starting and minimum learning-rates "eta" and min_eta specified. 
        The learning rate decreases over the epoches at every flag until it reaches 'min_eta'.
        The dropout value is the proportion of randomly desactivated neurons at each training iteration. It adds sturdiness to the model and reduces overfitting.
        You can add "test-data" to test your Network's performance and track it after each epoch.
        If you specify verbose = True, the training info will be displayed after each flag
        After the training, if the "optimize_accuracy" variable is set to True, the kept model state will be the one which scored the highest accuracy on the Test Data during the training
        """
        #formatting the flags per epoch into a list
        flags_per_epoch = int(flags_per_epoch)
        len_mini_batches = int(len(training_data) / mini_batch_size)
        fpe = range(1, len_mini_batches, int(len_mini_batches / flags_per_epoch))
        fpe = [fp for fp in fpe]
        fpe.remove(0)
        training_data = list(training_data)
        n = len(training_data)
        print("\nBeginning of the standard SGD method.")
        print("The network will be trained with :\n- {0} epochs\n- a mini-batch size of {1}\n- a learning rate of eta = {2} (min_eta = {3})\n- {4} flags per epoch".format(epochs, mini_batch_size, eta, min_eta, flags_per_epoch))
        if dropout_value:
            print("- a dropout value of {}%\n".format(dropout_value * 100))
        #If there is some training data, we check the network's performance with random initialization, to have an idea of the starting point
        if test_data:
            test_data = list(test_data)
            n_test = len(test_data)
            accuracy = 100 * self.evaluate(test_data) / n_test
            accuracies = [accuracy]
            print("\nAccuracy of the model at this state (with random weights and biases) : {}%\n".format(accuracy))
        #This list will contain the states of the network at each training epoch (weights and biases)
        states = list()
        #The learning rate will decrease over epochs
        current_eta = eta
        for i in range(epochs):
            fpe_index = 0
            #For each epoch, we shuffle the training data to get different mini batches randomly extracted from the training set
            random.shuffle(training_data)
            mini_batches = [training_data[k:k+mini_batch_size] for k in range(0, n, mini_batch_size)]
            #And then we calculate the gradient, and apply the descent for each mini-batch
            for f,mini_batch in enumerate(mini_batches):
                self.update_mini_batch(mini_batch, current_eta, dropout_value)
                #We save the performances after each flag based on the number of flags per epoch given
                if (f + 1) % fpe[fpe_index] == 0:
                    message = "Epoch {0}/{1} : [mini-batch {2} / {3}]".format(i + 1, str(epochs), str(f + 1), str(len(mini_batches)))
                    if fpe_index != len(fpe) - 1:
                        fpe_index += 1
                    if test_data:
                        #After each epoch, we save the accuracy (and the state of the network)                    
                        accuracy = 100 * self.evaluate(test_data) / n_test
                        accuracies.append(accuracy)
                        states.append((accuracy, self.biases, self.weights))
                        message += " => Accuracy : {0}%".format(str(accuracy))
                    if Verbose:
                        print(message)
                    if current_eta >= min_eta:
                        #We adjust the learning rate based on the learning speed of the training process 
                        if test_data:
                            #If we have test data, we proportionally decrease the learning rate with respect to the accuracy evolution observed
                            current_eta *= (1 - ((accuracy - (sum(accuracies) / len(accuracies))) / 100))
                        else:
                            current_eta *= 0.9
            if test_data: 
                #We display the evaluated accuracy after each epoch with the current learning rate
                print("\nEpoch n°{0} completed. Accuracy of the model at this state : {1}%, eta = {2:.2f}\n".format(i + 1, accuracy, current_eta))
            else:
                print("\nEpoch n°{0} completed.".format(i))                
        if test_data:
            #After the training, we plot a summary of the training process
            self.plot_accuracy_graph(mini_batch_size, eta, flags_per_epoch, accuracies, dropout_value)
            if optimize_accuracy:
                #And if specified, keep the best performing of all the states which occured during the training 
                saved_state = sorted(states)[-1]
                self.biases, self.weights = (saved_state[1], saved_state[2])
            
    def update_mini_batch(self, mini_batch, eta, dropout_value):
        """This method applies the SGD to each weight and bias of the network given a mini-batch of training examples"""
        #We sum the delta_nablas (gradients of the cost function with respect to each weight and bias in the network) over all the training examples in the mini-batch
        nabla_b = [np.zeros(b.shape) for b in self.biases]
        nabla_w = [np.zeros(w.shape) for w in self.weights]
        for x, y in mini_batch:
            #All the partial derivatives for each weight and each bias are calculated via backpropagation
            delta_nabla_b, delta_nabla_w = self.backprop(x, y, dropout_value)
            #We sum them
            nabla_b = [nb + dnb for nb, dnb in zip(nabla_b, delta_nabla_b)]
            nabla_w = [nw + dnw for nw, dnw in zip(nabla_w, delta_nabla_w)]
        #And dividing the sum to get a mean over the mini_batch, we apply a stochastic gradient descent to each weight and bias of the network (according to the learning rate)
        self.biases = [b - eta * (nb / len(mini_batch)) for b, nb in zip(self.biases, nabla_b)]
        self.weights = [w - eta * (nw / len(mini_batch)) for w, nw in zip(self.weights, nabla_w)]
        #Note : this method relies on the fact that our training data is homogeneous enough to let us assume that the mean of the gradient over a mini_batch is close to the mean over the whole dataset.
        #In the same way, it also relies on the fact that our learning rate isn't too high, to keep the differential approximation good enough, ensuring an increasing accuracy overtime.

    def backprop(self, x, y, dropout_value):
        """
        This method returns the gradient of the quadratic cost function (a function representing the square of the distance between the wanted output and the current network's output)
        The gradient is calculated with respect to each weight and each bias of each neuron in the network for a given training example x and its wanted output y (both are column matrixes).
        The returned gradient is a tuple of (the gradient with respect to the biases, the gradient with respect to the weights)
        The two parts of the returned gradient are lists of matrixes shaped respectively like the biases and weights matrixes of the network instance
        """
        #initialization of the two gradient parts 
        delta_nabla_b = [np.zeros(b.shape) for b in self.biases]
        delta_nabla_w = [np.zeros(w.shape) for w in self.weights]
        activation = x
        activations = [x] # list to store all the activations, layer by layer
        zs = [] #list to store all the z vectors, layer by layer
        #z = w.a + b and we feed z into the activation function (activation(z) = x)
        #We need to have access to each input and each output of each neuron of the network to apply the backpropagation algorithm. Hence, we:
        # - calculate each w.x+b = z at each layer and store them in zs as a list of column matrixes
        # - store sigmoid(z) in the activations list for each layer (and apply dropout if specified)
        for b, w in zip(self.biases, self.weights):
            z = np.dot(w, activation)+b
            zs.append(z)
            activation = self.activation_function(z)
            #We apply dropout at this moment, setting some of the activations to zero (theese will have a zero gradient)
            if dropout_value:
                activation = self.dropout(activation, dropout_value)
            activations.append(activation)
        #Once we have calculated the zs ans activations, we can start backpropagating
        #First, we calculate the gradient of the output layer with a chain rule
        #delta is the product of : the partial derivative of the quadratic cost with respect to the output of the regulation function,
        #the partial derivative of the regulation function with respect to the activation function outputs, and the partial derivative of the activations with respect to the inputs z=w.x+b
        delta = self.quadratic_cost_derivative(self.regu(activations[-1]), y) * self.regu_derivative(activations[-1]) * self.activation_function_derivative(zs[-1])
        #the partial derivative of the input z=w.x+b with respect to the biases is always 1. Hence, dCost/db = delta
        delta_nabla_b[-1] = delta
        #the partial derivative of the input z=w.x+b with respect to the weights is the sum of the outputs of the last layer for each output neuron. Hence, dCost/dw = delta * sum(activations_of_last_layer) -> matrix product [(n,1) * (1,n) = (n,n)]
        delta_nabla_w[-1] = np.dot(delta, activations[-2].transpose())
        #Then, for each layer from the lasts to the firsts, we backpropagate the partial derivatives
        for l in range(2, self.num_layers): #For each hidden layer
            #We retrieve the input activations z=w.x+b
            z = zs[-l]
            #And store the partial derivatives of the activation function with respect to the activation
            sp = self.activation_function_derivative(z)
            #With this data in hand, we can calculate a new derivative of the cost with respect to the output of the current hidden layer.
            #The delta of the current layer is equal to sp * the sum of the products of the delta of the next layer and the weights of the next layer -> matrix product
            #We use the transpose weights matrix because we want to calculate delta for each neuron of the lth layer regarding its synapses which link it to the l+1th layer
            delta = np.dot(self.weights[-l + 1].transpose(), delta) * sp
            #Once again, with delta in hand, the partial derivative of each bias with respect to the input activation is 1 -> the partial derivative is delta
            delta_nabla_b[-l] = delta
            #And in the same way, the partial derivative of the weights with respect to the input activation z=w.x+b, is the sum of the activations of the precedent layer -> matrix product
            delta_nabla_w[-l] = np.dot(delta, activations[-l - 1].transpose())
        #In the end, each matrix of the gradient has been calculated, we can return the gradient for the training example x,y
        return (delta_nabla_b, delta_nabla_w)

    def activation_function(self, x):
        """This method computes the network's outputs activation function (sigmoid,relu,tanh)"""
        if self.activation_function_name == 'sigmoid':
            return 1 / (1 + np.exp(-x))
        elif self.activation_function_name == 'relu':
            return np.maximum(0,x)
        elif self.activation_function_name == 'tanh':
            return np.tanh(x)

    def activation_function_derivative(self, x):
        """This method computes the derivative of the network's outputs activation function (sigmoid,relu,tanh)"""
        if self.activation_function_name == 'sigmoid':
            #sigmoid' = sigmoid(1 - sigmoid)
            return self.activation_function(x) * (1 - self.activation_function(x))
        elif self.activation_function_name == 'relu':
            derivs = []
            for activation in x:
                if activation <= 0:
                    derivs.append(0)
                else:
                    derivs.append(1)
            #relu' = 0 if x <= 0 and relu' = 1 if x > 0
            return np.array(derivs).reshape(x.shape)
        elif self.activation_function_name == 'tanh':
            #tanh' = 1 - tanh²
            return 1 - self.activation_function(x) * self.activation_function(x)

    def regu(self, x):
        """This method computes the network's output regulation function (softmax,normalization,none)"""
        #We catch the normalization/softmax errors because they generate exploding/vanishing output values sometimes, resulting in value errors
        with warnings.catch_warnings():
            warnings.filterwarnings('error')
            try:
                if not self.regu_name:
                    return x
                elif self.regu_name == 'normalization':
                    sum = np.sum(x) 
                    if sum != 0: #We have to check wether the activations are null to avoid a ZeroDivisionError (even if it is very unlikely)
                        return x / np.sum(x) 
                    else:
                        return x
                elif self.regu_name == 'softmax':
                    exps = np.exp(x)
                    sum = np.sum(exps)
                    if sum != 0:
                        return exps / np.sum(exps)
                    else:
                        return x
            except Warning: 
                if self.regu_name == 'softmax': 
                    print("softmax error : exps = ", exps)
                elif self.regu_name == 'normalization':
                    print("normalization error : np.sum(x) = ",np.sum(x), '\nx = ', x)
                elif not self.regu_name:
                    print(x)

    def regu_derivative(self, x):
        """This method computes the derivative of the network's output regulation function (softmax,normalization,none)"""
        if not self.regu_name:
            #No influence
            return 1
        elif self.regu_name == 'softmax':
            if sum(x): #making sure there is no 0/infinite output problem
                #softmax' = softmax(1 - softmax)
                return self.regu(x) * (1 - self.regu(x))
            else:
                return 1                
        elif self.regu_name == 'normalization':
            if sum(x):                
                #norm' = (sum(x) - x) / sum(x)²
                return (1 / sum(x)) * (1 - self.regu(x))
            else: #If the output activations are zero, the derivative is set to 0 to simplify (very unlikely)
                return 1

    def quadratic_cost_derivative(self, output_activations, y):
        """This method returns the derivative of the quadratic cost function with respect to the output activations of the last layer"""
        return (output_activations - y)

    def dropout(self, x, dropout_value):
        """This method applies dropout on the layer's activations vector "x". It also compensates the activation loss by proportionally boosting the activated outputs"""
        return x * (np.random.binomial([np.ones((len(x),1))], 1 - dropout_value) * (1.0 / (1 - dropout_value))).reshape((len(x),1))

    def evaluate(self, test_data):
        """This method is used to evaluate the accuracy of the model during its training on a given test data-set"""
        #The "test_results" array contains tuples of (index of the network's highest neuron output, wanted index)
        test_results = [(np.argmax(self.feedforward(x)), y) for x,y in test_data]
        return sum(int(x == y) for x,y in test_results)

    def __repr__(self):
        """We represent a network instance simply by its identifier, its shape, and activation/regulation functions"""
        return "Neural network -> " + str(self.id) + " : " + str(self.sizes) + ", activation function : " + str(self.activation_function_name) + ", output regulation method : " + str(self.regu_name)

    def plot_accuracy_graph(self, mini_batch_size, eta, fpe, accuracies, dropout_value):
        """This method is executed right after the end of a network training. It plots a summary of the training process, and saves it into a png file"""
        plt.figure(figsize = (8, 8))
        x = range(len(accuracies))
        plt.plot(x, accuracies)
        if not dropout_value:
            dropout_value = ""
        else:
            dropout_value = "dropout = " + str(dropout_value)
        plt.title("Training of the model \"{0}\" ({1}): mini_batch_size = {2}, eta = {3}, {4}".format(self.id, self.activation_function_name, mini_batch_size, eta, dropout_value))
        plt.xlabel("Epoch completions")
        plt.ylabel("Accuracy (measured on the test data)")
        axes = plt.gca()
        axes.set_ylim([0, 100])
        ticks = np.array(range(0, len(accuracies), fpe))
        plt.xticks(ticks, np.array(ticks/fpe, dtype='int'))
        plt.yticks(range(0,101,10))
        annot_max(x, np.array(accuracies), axes, fpe)
        plt.savefig("trainings/training_{}/training_graph".format(str(t)))


#plot max annotation
def annot_max(x, y, ax, fpe):
    xmax = x[np.argmax(y)]
    ymax = y.max()
    text = "max accuracy = {:.2f}%, at epoch {}".format(ymax, ceil(xmax / fpe) )        
    if not ax:
        ax=plt.gca()
    bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
    arrowprops=dict(arrowstyle="->",connectionstyle="angle,angleA=0,angleB=60")
    kw = dict(xycoords='data',textcoords="axes fraction",
            arrowprops=arrowprops, bbox=bbox_props, ha="right", va="top")
    ax.annotate(text, xy=(xmax, ymax), xytext=(0.9, 0.85), **kw)

