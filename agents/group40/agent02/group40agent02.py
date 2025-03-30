import logging
from decimal import Decimal
from random import randint
from time import time
from typing import cast, Dict

from geniusweb.actions.Accept import Accept
from geniusweb.actions.Action import Action
from geniusweb.actions.Offer import Offer
from geniusweb.actions.PartyId import PartyId
from geniusweb.bidspace.AllBidsList import AllBidsList
from geniusweb.inform.ActionDone import ActionDone
from geniusweb.inform.Finished import Finished
from geniusweb.inform.Inform import Inform
from geniusweb.inform.Settings import Settings
from geniusweb.inform.YourTurn import YourTurn
from geniusweb.issuevalue.Bid import Bid
from geniusweb.issuevalue.Domain import Domain
from geniusweb.party.Capabilities import Capabilities
from geniusweb.party.DefaultParty import DefaultParty
from geniusweb.profile.utilityspace.LinearAdditiveUtilitySpace import (
    LinearAdditiveUtilitySpace,
)
from geniusweb.profileconnection.ProfileConnectionFactory import (
    ProfileConnectionFactory,
)
from geniusweb.progress.ProgressTime import ProgressTime
from geniusweb.references.Parameters import Parameters
from geniusweb.utils import toStr
from tudelft_utilities_logging.ReportToLogger import ReportToLogger

from .utils.opponent_model import OpponentModel, IssueEstimator


class Group40Agent02(DefaultParty):
    """
    Template of a Python geniusweb agent.
    """

    def __init__(self):
        super().__init__()
        self.logger: ReportToLogger = self.getReporter()

        self.domain: Domain = None
        self.parameters: Parameters = None
        self.profile: LinearAdditiveUtilitySpace = None
        self.progress: ProgressTime = None
        self.me: PartyId = None
        self.other: str = None
        self.settings: Settings = None
        self.storage_dir: str = None

        self.last_received_bid: Bid = None
        self.opponent_model: OpponentModel = None
        self.logger.log(logging.INFO, "party is initialized")

        # OUR PARAMETERS
        # time_to_bid: map of time (in range [0,1]) to the opponent bid that was offered at that time
        self.time_to_bid: Dict[float, Bid] = {}

    def notifyChange(self, data: Inform):
        """MUST BE IMPLEMENTED
        This is the entry point of all interaction with your agent after is has been initialised.
        How to handle the received data is based on its class type.

        Args:
            info (Inform): Contains either a request for action or information.
        """

        # a Settings message is the first message that will be send to your
        # agent containing all the information about the negotiation session.
        if isinstance(data, Settings):
            self.settings = cast(Settings, data)
            self.me = self.settings.getID()

            # progress towards the deadline has to be tracked manually through the use of the Progress object
            self.progress = self.settings.getProgress()

            self.parameters = self.settings.getParameters()
            self.storage_dir = self.parameters.get("storage_dir")

            # the profile contains the preferences of the agent over the domain
            profile_connection = ProfileConnectionFactory.create(
                data.getProfile().getURI(), self.getReporter()
            )
            self.profile = profile_connection.getProfile()
            self.logger.log(logging.INFO, "Utilities: " + toStr(self.profile.getUtilities()))
            self.logger.log(logging.INFO, "Weights: " + toStr(self.profile.getWeights()))
            self.domain = self.profile.getDomain()
            profile_connection.close()


        # ActionDone informs you of an action (an offer or an accept)
        # that is performed by one of the agents (including yourself).
        elif isinstance(data, ActionDone):
            action = cast(ActionDone, data).getAction()
            actor = action.getActor()

            # ignore action if it is our action
            if actor != self.me:
                # obtain the name of the opponent, cutting of the position ID.
                self.other = str(actor).rsplit("_", 1)[0]

                # process action done by opponent
                self.opponent_action(action)
        # YourTurn notifies you that it is your turn to act
        elif isinstance(data, YourTurn):
            # execute a turn
            self.my_turn()

        # Finished will be send if the negotiation has ended (through agreement or deadline)
        elif isinstance(data, Finished):
            self.save_data()
            # terminate the agent MUST BE CALLED
            self.logger.log(logging.INFO, "party is terminating:")
            super().terminate()
        else:
            self.logger.log(logging.WARNING, "Ignoring unknown info " + str(data))

    def getCapabilities(self) -> Capabilities:
        """MUST BE IMPLEMENTED
        Method to indicate to the protocol what the capabilities of this agent are.
        Leave it as is for the ANL 2022 competition

        Returns:
            Capabilities: Capabilities representation class
        """
        return Capabilities(
            set(["SAOP"]),
            set(["geniusweb.profile.utilityspace.LinearAdditive"]),
        )

    def send_action(self, action: Action):
        """Sends an action to the opponent(s)

        Args:
            action (Action): action of this agent
        """
        self.getConnection().send(action)

    # give a description of your agent
    def getDescription(self) -> str:
        """MUST BE IMPLEMENTED
        Returns a description of your agent. 1 or 2 sentences.

        Returns:
            str: Agent description
        """
        return "Agent01 of group 40."

    def opponent_action(self, action):
        """Process an action that was received from the opponent.

        Args:
            action (Action): action of opponent
        """
        # if it is an offer, set the last received bid
        if isinstance(action, Offer):
            # create opponent model if it was not yet initialised
            if self.opponent_model is None:
                self.opponent_model = OpponentModel(self.domain)

            bid = cast(Offer, action).getBid()
            progress = self.progress.get(time() * 1000)


            # add the opponent's bid to our time_to_bid dictionary
            self.time_to_bid[progress] = bid

            # update opponent model with bid
            self.opponent_model.update(bid)
            # set bid as last received
            self.last_received_bid = bid

    def my_turn(self):
        """This method is called when it is our turn. It should decide upon an action
        to perform and send this action to the opponent.
        """
        # check if the last received offer is good enough
        if self.accept_condition(self.last_received_bid):
            # if so, accept the offer
            action = Accept(self.me, self.last_received_bid)
        else:
            # if not, find a bid to propose as counter offer
            bid = self.find_bid()
            action = Offer(self.me, bid)

        # send the action
        self.send_action(action)

    def save_data(self):
        """This method is called after the negotiation is finished. It can be used to store data
        for learning capabilities. Note that no extensive calculations can be done within this method.
        Taking too much time might result in your agent being killed, so use it for storage only.
        """
        data = "Data for learning (see README.md)"
        with open(f"{self.storage_dir}/data.md", "w") as f:
            f.write(data)

    # calculate the maximum utility of the recorded opponent bids
    # where the bid was offered after start
    def _calc_max_w(self, start) -> Decimal:
        curr_max = Decimal(0.0)
        for t, bid in self.time_to_bid.items():
            if t >= start:
                curr_max = max(curr_max, self.profile.getUtility(bid))
        return curr_max

    # calculate the average utility of the recorded opponent bids
    # where the bid was offered after start
    def _calc_avg_w(self, start) -> Decimal:
        curr_sum = Decimal(0.0)
        n = 0
        for t, bid in self.time_to_bid.items():
            if t >= start:
                curr_sum += self.profile.getUtility(bid)
                n += 1
        return curr_sum / Decimal(n) if n else Decimal(0.0)

    def accept_condition(self, bid: Bid) -> bool:
        if bid is None:
            return False

        from time import time
        progress = self.progress.get(time() * 1000)

        # here 'next' refers to the bid that we will put out next
        our_next_bid = self.find_bid()
        our_next_util = self.profile.getUtility(our_next_bid)
        opponent_bid_util = self.profile.getUtility(bid)

        # PHASE 1, before 30% of the negotiation is done
        if progress < 0.3:
            return opponent_bid_util >= our_next_util * Decimal(1.02) # 2% more than what we want increase

        # PHASE 2, 30%-60% of the negotiation is done
        if progress < 0.6:
            return opponent_bid_util >= our_next_util

        # PHASE 3, after 60% of the negotiation is done but before negotiation is finished
        if progress < 0.99:
            # calculate the starting time (in range [0,1]) of the window of bids
            r = Decimal(1.0) - Decimal(progress)
            w_start = Decimal(progress) - r

            # calculate the utility threshold
            util_threshold = self._calc_max_w(w_start)
            return opponent_bid_util >= our_next_util or opponent_bid_util >= util_threshold

        # PHASE 4, after 99% of the negotiation is done, always accept the (final) offer
        return True

    def find_bid(self) -> Bid:
        # compose a list of all possible bids
        domain = self.domain
        progress = self.progress.get(time() * 1000)
        eps = 0.2
        time_pressure = Decimal(str(2.0 - progress ** (1 / eps)))

        our_weights = self.profile.getWeights()
        our_utilities = self.profile.getUtilities()

        opponent_weights = self.profile.getWeights() # TODO Use opponent model
        opponent_utilities = self.profile.getUtilities() # TODO Use opponent model

        all_values = dict()
        for issue in domain.getIssues():
            curr_values = dict()

            our_weight = our_weights.get(issue)
            our_preference = our_utilities.get(issue)

            opponent_weight = opponent_weights.get(issue)
            opponent_preference = opponent_utilities.get(issue)
            for value in domain.getValues(issue):
                curr_values[value] = (time_pressure * our_weight * our_preference.getUtility(value)) + (opponent_weight * opponent_preference.getUtility(value))

            all_values[issue] = max(curr_values, key=curr_values.get)


        return Bid(all_values)

    def score_bid(self, bid: Bid, alpha: float = 0.95, eps: float = 0.1) -> float:
        """Calculate heuristic score for a bid

        Args:
            bid (Bid): Bid to score
            alpha (float, optional): Trade-off factor between self interested and
                altruistic behaviour. Defaults to 0.95.
            eps (float, optional): Time pressure factor, balances between conceding
                and Boulware behaviour over time. Defaults to 0.1.

        Returns:
            float: score
        """
        progress = self.progress.get(time() * 1000)

        our_utility = float(self.profile.getUtility(bid))

        time_pressure = 1.0 - progress ** (1 / eps)
        score = alpha * time_pressure * our_utility

        if self.opponent_model is not None:
            opponent_utility = self.opponent_model.get_predicted_utility(bid)
            opponent_score = (1.0 - alpha * time_pressure) * opponent_utility
            score += opponent_score

        return score
