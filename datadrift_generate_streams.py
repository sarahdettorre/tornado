import random
import pickle
import itertools
import os

from streams.generators.__init__ import *


def get_parameter_list(equal_concept_length, equal_transition_length, max_num_drifts):

    """Gets the list of parameter dictionaries for generating streams.

    Parameters:
    equal_concept_lenth (bool): If true, each parameter configuration will have concepts of equal length. Otherwise, each configuration will have a random combination of the possible lengths."
    equal_transition_lenth (bool): If true, each parameter configuration will have transitions of equal length. Otherwise, each configuration will have a random combination of the possible lengths."
    max_num_drifts (int): the maximum number of drifts that can occur per stream.

    Returns:
    list of dictionaries: A list of dictionaries of parameters for generating streams.

   """
    parameter_list = []

    concept_length_list = [1000,10000,25000]
    transition_length_list = [500,1000,10000]
    noise_ratio_list = [0.0,0.1,0.2,0.3]
    magnitude_list = [1,2,3,4,5,6,7]


    for num_drifts in range(1, max_num_drifts + 1):
        for magnitude_combination in itertools.combinations(magnitude_list, num_drifts + 1):  
            for concept_len in concept_length_list: #if equal_concept_length is false, don't necessarily have to go through this loop, but it does limit iterations
                for transition_len in transition_length_list: #if equal_transition_length is false, don't necessarily have to go through this loop, but it does limit iterations
                    for noise_ratio in noise_ratio_list:
                        parameter_list.append({'concept_length':[concept_len]*(num_drifts + 1) if equal_concept_length else list(random.choice(list(itertools.combinations_with_replacement(concept_length_list, num_drifts + 1)))), #the duration of the concept, for each concept in the stream
                                                'led_attr_drift': list(magnitude_combination), #the number of attributes which drift within each concept
                                                'transition_length':[transition_len]*num_drifts if equal_concept_length else list(random.choice(list(itertools.combinations_with_replacement(transition_length_list, num_drifts)))), #the length of the transition period from one concept to another (shorter is more abrupt, longer is gradual)
                                                'noise_rate':noise_ratio, #the ratio of rows that will include a flipped bit on one of the relevant attributes and/or an incorrect class label
                                                'num_irr_attr': 17, #the number of irrelevant attributes to add
                                                'led_attr_noise': list(range(0, 7)), #the indices of the attributes which can take on noise (defualt is all relevant attributes)
                                                'led_target_noise': False, #a flag indicating whether or not noise should be injected into the target attribute
                                                'random_seed': random.choice(list(range(0,1000))) #the random seed for the stream
                                                })
                        #print(parameter_list)
                        #exit()

    #print(len(parameter_list))
    #exit()

    return parameter_list

def generate_stream(parameter_dict, file_path):

    """Generates a synthetic stream and saves it.

    Parameters:
    parameter_dict (dictionary): The dictionary holding all parameters for stream generation.
    file_path (string): The path where the stream file should be saved.

    Returns:
    LEDConceptDrift object: The stream generator object.

   """

    #generate the stream
    stream_generator = LEDConceptDrift(parameter_dict['concept_length'], 
                                        parameter_dict['num_irr_attr'], 
                                        parameter_dict['led_attr_drift'],
                                        parameter_dict['transition_length'],
                                        parameter_dict['noise_rate'],
                                        parameter_dict['led_attr_noise'],
                                        parameter_dict['led_target_noise'],
                                        parameter_dict['random_seed'])

    #save the stream as arff file
    stream_generator.generate(file_path)

    return stream_generator

def save_metadata(stream_generator, parameter_dict, meta_path):

    """Saves the metadata of the stream. Includes all generation parameters plus some computed meta data.

    Parameters:
    stream_generator (LEDConceptDrift onject): The generator object for the stream.
    parameter_dict (dictionary): The dictionary holding all parameters for stream generation.
    meta_path (string): The path where the meta data should be saved.

   """

    #compute the stream's meta data
    drift_locations = []
    pointer = 0
    for concept_len, transition_len in zip(parameter_dict['concept_length'][:-1],parameter_dict['transition_length']):
        start = pointer + concept_len
        end = start + transition_len
        drift_locations.append([start,end])
        pointer = end
    

    meta_dict = {'total_len':stream_generator.get_total_len(),
                'num_drifts':len(parameter_dict['transition_length']), 
                'drift_locations':drift_locations,
                'noise_locations':stream_generator.get_noise_locations(),
                'equal_concept_length': True if all(x==parameter_dict['concept_length'][0] for x in parameter_dict['concept_length']) else False,
                'equal_transition_length': True if all(x==parameter_dict['transition_length'][0] for x in parameter_dict['transition_length']) else False
                }

    #add the parameter list to the meta_dict
    meta_dict.update(parameter_dict)

    #output to pickle
    meta_pickle_file = open(meta_path, 'wb') 
    pickle.dump(meta_dict, meta_pickle_file)
    meta_pickle_file.close()

def generate_multiple_streams(equal_concept_length, equal_transition_length, max_num_drifts):

    """Generates multiple streams at once with multiple combinations of parameters.

    Parameters:
    equal_concept_lenth (bool): If true, each parameter configuration will have concepts of equal length. Otherwise, each configuration will have a random combination of the possible lengths."
    equal_transition_lenth (bool): If true, each parameter configuration will have transitions of equal length. Otherwise, each configuration will have a random combination of the possible lengths."
    max_num_drifts (int): the maximum number of drifts that can occur per stream.

   """

    parameter_list = get_parameter_list(equal_concept_length, equal_transition_length, max_num_drifts)

    count = 0
    for parameter_dict in parameter_list:

        stream_name = "led_"+str(count)
        project_path = PROJECT_PATH + stream_name + "/"
        if not os.path.exists(project_path):
            os.makedirs(project_path)
        file_path = project_path + stream_name
        meta_path = project_path + stream_name + ".pickle"

        stream_generator = generate_stream(parameter_dict, file_path)
        save_metadata(stream_generator, parameter_dict, meta_path)

        count +=1


def generate_ad_hoc_stream(stream_name, concept_length = [25000,25000,25000,25000], led_attr_drift= [1,3,2,5],transition_length=[500,500,500],noise_rate=0.1,num_irr_attr= 17,
    led_attr_noise = list(range(0, 7)),led_target_noise = False,random_seed = random.choice(list(range(0,1000)))):

    """Generates a single ad hoc stream, saves it and its meta data.

    Parameters:
    concept_lenth (list): the duration of the concept, for each concept in the stream
    led_attr_drift (list): the number of attributes which drift within each concept
    transition_length (list): the length of the transition period from one concept to another (shorter is more abrupt, longer is gradual)
    noise_rate (float between 0 and 1): the ratio of rows that will include a flipped bit on one of the relevant attributes and/or an incorrect class label
    num_irr_attr (int): the number of irrelevant attributes to add 
    led_attr_noise (list): the indices of the attributes which can take on noise (defualt is all relevant attributes)
    led_target_noise (bool): a flag indicating whether or not noise should be injected into the target attribute
    random_seed (int): the random seed for the stream

   """

    project_path = PROJECT_PATH + stream_name + "/"
    if not os.path.exists(project_path):
        os.makedirs(project_path)
    file_path = project_path + stream_name
    meta_path = project_path + stream_name + ".pickle"
    
    parameter_dict = {'concept_length':concept_length, 
                        'led_attr_drift': led_attr_drift, 
                        'transition_length':transition_length, 
                        'noise_rate':noise_rate, 
                        'num_irr_attr': num_irr_attr, 
                        'led_attr_noise': led_attr_noise, 
                        'led_target_noise': led_target_noise, 
                        'random_seed': random_seed 
                        }
    stream_generator = generate_stream(parameter_dict, file_path)
    save_metadata(stream_generator, parameter_dict, meta_path)



global PROJECT_PATH
PROJECT_PATH = "data_streams/synthetic/"

#generate multiple streams for an experiment
generate_multiple_streams(equal_concept_length = True, equal_transition_length = True, max_num_drifts = 5)
generate_multiple_streams(equal_concept_length = False, equal_transition_length = False, max_num_drifts = 5)


#ad hoc stream generation
#generate_ad_hoc_stream('led_test')


