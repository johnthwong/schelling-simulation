# Name: John T.H. Wong
# Hardware: Macbook Air, M1, 2020
# OS: MacOS 14.4
# SDE: VS Code, 1.91.1 (Universal)

import random, uuid
import pandas as pd

class Agent:
    def __init__(self, max_prejudice):
        # Agents have two attributes of interest for us. 
        # (1) Which identity group--such as race--they are and
        # (2) Their preferred level of homogeneity, which we call prejudice.
        # (3) A unique ID to track each agent independently of where they live.

        # Randomize between two identities, A or B
        self.__identity = random.choice(['A', 'B'])
        # Randomize prejudice level to create heterogeneity
        self.__prejudice = random.uniform(0, max_prejudice)
        # Create unique ID
        self.__id = uuid.uuid4()
    
    # These functions return the three attributes.
    def getIdentity(self):
        return self.__identity
    
    def getPrejudice(self):
        return self.__prejudice
    
    def getID(self):
        return self.__id


class Tract:
    def __init__(self):
        # We want to simultaneously initiate the tract and the agent that lives there.
        # Each agent must live on a tract. Thus, they are stored in the Tract.resident attribute.
        # Agents can only be called through a tract.

        # The following if statement randomizes whether an agent is initiated.
        # We leave 10 percent of tracts unresided so that agents have room to move.

        # Create a uniform random variable.
        self.runningVariable = random.uniform(0, 1)

        # The tract is left empty with a ten percent chance (if the random variable exceeds 0.9).
        if self.runningVariable >= 0.9:
            self.__filled = 0
            self.resident = None
        # Otherwise, we create an agent.
        else:
            # Set the Tract.__filled attribute to 1.
            self.__filled = 1
            # Initialize Agent, and store it under resident.
            # Let agent draw a prejudice level between 0 and 0.7.
            self.resident = Agent(0.7)

    # This function calls for the Tract.filled attribute.
    def getResidence(self):
        return self.__filled

class City:
    def __init__(self):
        # Initialize a City object.

        # The city is the object that holds all the Tracts. The Tracts are stored under City.__tracts.
        self.__tracts = []
        # We also track two other tract-level attributes:
        # 1. We want to know how homogeneous a Tract is for the Agent who lives there. 
        self.__homogeneityToResident = []
        # 2. We want to know how happy the Tract's current Agent is.
        self.__happiness = []

        # Set up dictionary to collect data on moves.
        self.moveData = {
            'moveIndex': [],
            'movingAgentID': [],
            'originTractIndex': [],
            'destinationTractIndex': [],
            'unhappyCount': [],
            'avgHomogeneity': []
        }

    def generateTracts(self, length):
        # This function initializes the tracts, which in turn initializes the agents.
        # The length argument sets how big the City is. Note that the City is a straight line. 
        # If there are 1000 tracts, then the length of the city is 1000.

        # The length of the city is stored as a city-level attribute.
        self.__cityLength = length
        # We also hard-code the radius of the neighbood.
        # This sets how far the Agent looks to determine their neighborhood homogeneity.
        self.__neighborDist = 3

        # The following loop creates as many tracts as the city length and appends them to the self.__tracts.
        self.__tracts = []
        for i in range(length):
            self.__tracts.append(Tract())

    def executeMoves(self):
        # This is the function around which the module is built.
        # This function moves agents until there are no more unhappy agents.
        # It works in the following procedure
        # 1. Determine which tract contains unhappy agents
        # 2. Determine which tracts are empty
        # 3. For each agent who is unhappy:
        # 3a. The agent evaluates the homogeneity of empty tracts. This needs to be calculated for each agent.
        # 3b. The agent filters the list of empty tracts for those with satisfactory homogeneity.
        # 3c. The agent moves to a random satisfactory tract.
        # 4. We set the chosen empty tract's resident to the agent.
        # 5. We empty the origin tract.
        # 6. The arrival of the new agent will surrounding happiness, so we survey which tracts contain unhappy agents again.
        # 7. Calculate aggregate homogeneity.
        # 8. Repeat steps 1-7 until there are no more unhappy agents.

        # Survey happiness. This gives us a list of tracts with (un)happy residents.
        self.surveyHappiness()
        # Survey availability. This gives us a list of empty tracts.
        self.surveyAvailability()

        # empty the moveData dictionary
        self.moveData = {
            'moveIndex': [],
            'movingAgentID': [],
            'originTractIndex': [],
            'destinationTractIndex': [],
            'unhappyCount': [],
            'avgHomogeneity': []
        }

        # Deal with unhappy agents
        # While not all agents are happy
        iterationCount = 0
        while sum(self.__happiness) < self.__cityLength:
            # Use a list comprehension to get the positions of the tracts with unhappy agents.
            unhappyAgents = [i for i, value in enumerate(self.__happiness) if value == 0]

            # Choose a random unhappy agent to start with.
            agentIndex = random.choice(unhappyAgents)
            
            # Determine their origin tract, identity, and prejudice.
            originTract = self.__tracts[agentIndex]
            agentIdentity = originTract.resident.getIdentity()
            agentPrejudice = originTract.resident.getPrejudice()
            agentID = originTract.resident.getID()

            # Use a list comprehension to get the positions of empty tracts.
            emptyTractsIndex = [i for i, value in enumerate(self.__availability) if value == 0]
            
            # Set up a dictionary to track each empty tract's homogeneity *from the perspective of the mover*.
            tractCatalog = {
                'index' : emptyTractsIndex,
                'homogeneityToMover' : []
            }

            # Loop over the empty tracts to calculate each tract's homogeneity.
            for prospectiveTractIndex in emptyTractsIndex:
                # Locate the prospective tract object.
                prospectiveTract = self.__tracts[prospectiveTractIndex]
                # Use self.getHomogeneity() to determine the tract's homogeneity to the mover.
                tractHomogeneity = self.genHomogeneity(prospectiveTract, agentIdentity)
                # Record result into the dictionary.
                tractCatalog['homogeneityToMover'].append(tractHomogeneity)
            
            # Turn the dictionary into a dataframe so we can query it. Create a narrower dataframe of "valid" tracts.
            tractDataframe = pd.DataFrame(tractCatalog)
            validTracts = tractDataframe.query('homogeneityToMover >= @agentPrejudice')

            # Make sure the dataframe is not empty. If it is, skip the agent.
            if not validTracts.empty:
                
                # Count the move
                iterationCount = iterationCount + 1
                self.moveData['moveIndex'].append(iterationCount)

                # Record the agent and their origin into our dictionary
                self.moveData['movingAgentID'].append(agentID)
                self.moveData['originTractIndex'].append(agentIndex)

                # Choose a random tract. Get its location in self.__tracts.
                # .tolist() returns a scalar. Like R's pull()
                chosenTractIndex = random.choice(validTracts['index'].tolist())
                # Record the destination into our dictionary
                self.moveData['destinationTractIndex'].append(chosenTractIndex)

                # Move the agent

                # Set the destination tract's resident as the moving agent.
                self.__tracts[chosenTractIndex].resident = originTract.resident
                # Update the tract-level availability attribute of the destination tract.
                self.__tracts[chosenTractIndex].__filled = 1
                # Delete agent from the origin tract.
                originTract.resident = None
                # Update availability attribute of the origin tract.
                originTract.__filled = 0

                # Run surveyAvailability() to update the city's tract-level availability list.
                self.surveyAvailability()
                # Run surveyHappiness() to update the city's tract-level happiness list.
                self.surveyHappiness()
                
                # Record count of unhappy residents into our dictionary
                # Note that sum(self.__happiness) includes empty units. 
                # So if we subtract it from self.__cityLength, we will get population of unhappy agents.
                self.moveData['unhappyCount'].append( self.__cityLength - sum(self.__happiness) )

                # Calculate and record and print average homogeneity.
                avgHomogeneity = sum(self.__homogeneityToResident)/sum(self.__availability)
                self.moveData['avgHomogeneity'].append(avgHomogeneity)
            else:
                continue
        
            if iterationCount == 1 or iterationCount % 50 == 0:
                print(f'Average homogeneity is at {avgHomogeneity}.')
                print(f'{1 - sum(self.__happiness) / self.__cityLength} of residents are unhappy.')
            else:
                continue

    def genNeighborsIndex(self, selectedTract, d: int, n: int) -> list:
        # HELPER FUNCTION
        # This function returns the index of neighbors for a given Tract object.

        # The -> list: syntax in Python is part of type hinting. It's used to specify the return type of a function.
        # This type hint is just for clarity and doesn't enforce type checking at runtime. 
        # It's meant to help developers understand what kind of value the function is expected to return.
        
        # Determine the tract's index.
        i = self.__tracts.index(selectedTract)
        
        """
        Returns a list of d integers to the left and right of i in a circular list of length n.
        
        :param i: The index to find neighbors for.
        :param d: The number of neighbors on each side.
        :param n: The length of the circular list.
        :return: A list of 2d neighbors.
        """

        # range(d, 0, -1). "-1" argument creates a descending list of integers. "0" means it ends at 1.
        # for j in x means iterate on x with j as the stand-in for each element.
        # (i-j) % n returns n + (i-j) if (i-j) is negative, (i - j) if (i-j) is positive, ...
        # because the remainder of (i - j) / n is just (i - j).
        # this logic works when (i - j) < 0 because python adds n to (i - j), and the result is always less than n.
        left_neighbors = [(i - j) % n for j in range(d, 0, -1)]
        right_neighbors = [(i + j) % n for j in range(1, d + 1)]
        
        return left_neighbors + right_neighbors
    
    def genHomogeneity(self, selectedTract, identity) -> float:
        # HELPER FUNCTION
        # This function measures the homogeneity of a tract. 
        # The homogeneity can be toResident or toMover. 
        # If an identity (e.g., "A") is specified in the identity argument, it calculates the homogeneity from the perspective of that identity.
        # If the identity argument is set to "current", it calculates the homogeneity of the tract relative to the current resident, if one exists.

        # Use self.genNeighborsIndex() to figure out the indices of the neighboring tracts.
        neighborsIndex = self.genNeighborsIndex(selectedTract, self.__neighborDist, self.__cityLength)

        # Determine which argument is fed into "identity":
        if identity == "current":
            if selectedTract.resident is None:
                return
            else:
                identityUsed = selectedTract.resident.getIdentity()
        else:
            identityUsed = identity
        
        # Homogeneity is defined as similarCount/neighborCount, or zero if there is no neighbor.
        neighborCount = 0
        similarCount = 0

        # Work through the list of neighbors
        for j in neighborsIndex:
            # Call the tract object of that index
            otherTract = self.__tracts[j]

            # Make sure it's not empty, otherwise continue
            if otherTract.resident is not None:
                neighborCount = neighborCount + 1

                # Determine whether the neighbor is of the same identity
                if identityUsed == otherTract.resident.getIdentity():
                    similarCount = similarCount + 1
                else:
                    continue
            else:
                continue
        
        if neighborCount != 0:
            tractHomogeneity = similarCount/neighborCount
        else:
            tractHomogeneity = 0
        
        return tractHomogeneity

    def surveyAvailability(self):
        # HELPER FUNCTION
        # Determine tract-level availability

        # Reset the availability list
        self.__availability = []

        # Append the Tract.__filled value of each tract.
        for tract in self.__tracts:
            self.__availability.append(tract.getResidence())
    
    def surveyHappiness(self):
        # HELPER FUNCTION
        # Calculate homogeneity for all agents and determine happiness

        # Reset homogeneity and happiness.
        self.__homogeneityToResident = [0] * self.__cityLength
        # Empty tracts have happiness = 1. This makes identifying tracts with unhappy agents easier.
        self.__happiness = [1] * self.__cityLength
        
        # Loop over every tract.
        for selectedTract in self.__tracts:

            # Get the index of the current tract.
            selectedTractIndex = self.__tracts.index(selectedTract)
            
            # Debug print statement
            # print(f'Checking tract at index {selectedTractIndex}')
            

            # Check whether there is a resident. If there isn't, set happiness to zero.
            if selectedTract.resident is not None:

                # Call the agent object.
                selectedAgent = selectedTract.resident

                # Debug print statement
                # print(f'Tract at index {selectedTractIndex} has a resident with identity {selectedAgent.getIdentity()}')

                # Use the genHomogeneity() function.
                tractHomogeneity = self.genHomogeneity(selectedTract, "current")
                
                # Debug print statement
                # print(f'Tract homogeneity for tract at index {selectedTractIndex}: {tractHomogeneity}')
                
                # Store the homogeneity result
                self.__homogeneityToResident[selectedTractIndex] = tractHomogeneity
                
                # Compare tract homogneity to agent's prejudice
                if tractHomogeneity < selectedAgent.getPrejudice():
                    self.__happiness[selectedTractIndex] = 0
                    # Debug print statement
                    # print(f'Resident at tract index {selectedTractIndex} is unhappy (Prejudice: {selectedAgent.getPrejudice()})')
                else:
                    self.__happiness[selectedTractIndex] = 1
                    # Debug print statement
                    # print(f'Resident at tract index {selectedTractIndex} is happy (Prejudice: {selectedAgent.getPrejudice()})')
            else:
                # Debug print statement
                # print(f'Tract at index {selectedTractIndex} has no resident')
                continue
        
        # Print unhappiness at the end.
        # print(f'{1 - sum(self.__happiness) / self.__cityLength} of residents are unhappy.')

    def surveyAvgPrejudice(self):
        aggregatePrejudice = 0

        # Loop over occupied tracts to get their resident's prejudice level
        for tract in self.__tracts:
            if tract.resident is None:
                continue
            else:
                aggregatePrejudice = aggregatePrejudice + tract.resident.getPrejudice()
        
        # Run surveyAvailability() to get an accurate population count
        self.surveyAvailability()

        population = sum(self.__availability)

        # Compute and return average prejudice
        avgPrejudice = aggregatePrejudice/population
        return avgPrejudice


