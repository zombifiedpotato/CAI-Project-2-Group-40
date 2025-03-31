import logging
import random
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


class Group40Agent04(DefaultParty):
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
        self.all_bids_utility: Dict[Bid, float] = dict()

        # last_my_turn_time: the progress value (in range [0, 1]) of when it was our turn last
        self.last_my_turn_time = None

        # max_time_for_turn: we keep the maximum time it takes for it to be our turn again so that we estimate
        # when it will be our last turn
        self.max_time_for_turn = 0.0

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
            self.domain = self.profile.getDomain()
            self.opponent_model = OpponentModel(self.domain)
            all_bids_list = AllBidsList(self.domain)
            print(all_bids_list.size())
            for i in range(0, all_bids_list.size() - 1):
                print(i)
                bid = all_bids_list.get(i)
                self.all_bids_utility[bid] = self.profile.getUtility(bid)

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
        return "Agent03 of group 40."

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

            # print("\n🔹 Opponent Estimated Issue Preferences 🔹")
            # for issue in self.domain.getIssues():
            #     try:
            #         issue_utilities = self.opponent_model.get_issue_value_utilities(issue)
            #         print(f"Issue: {issue}")
            #         for value, weight in issue_utilities.items():
            #             print(f"  - Value: {value}, Estimated Utility: {weight:.3f}")
            #     except ValueError:
            #         print(f"⚠️ Warning: Issue '{issue}' not found in opponent model.")
            # print("──────────────────────────────────────────\n")

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

        # update last_my_turn_time and max_time_for_turn
        progress = self.progress.get(time() * 1000)

        # if last_my_turn_time is None, we do not update max_time_for_turn, and only initialize last_my_turn_time
        if self.last_my_turn_time is None:
            self.last_my_turn_time = progress
            return

        self.max_time_for_turn = max(self.max_time_for_turn, progress - self.last_my_turn_time)
        self.last_my_turn_time = progress


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

    # Calculate the minimum utility of the recorded opponent bids
    # where the bid was offered after start
    def _calc_min_w(self, start) -> Decimal:
        curr_min = Decimal(1.0)
        for t, bid in self.time_to_bid.items():
            if t >= start:
                curr_min = min(curr_min, self.profile.getUtility(bid))
        return curr_min

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
        # Statistical parameters used
        min_val = 0.7
        max_val = 1.0
        epsilon = 0.2  # as specified in the article
        alpha = 1.02
        beta = 0.0
        rvalue_threshold = 0.1

        if bid is None:
            return False

        from time import time
        progress = self.progress.get(time() * 1000)

        # here 'next' refers to the bid that we will put out next
        our_next_bid = self.find_bid()
        our_next_util = self.profile.getUtility(our_next_bid)
        our_reservation_util = self.profile.getUtility(self.profile.getReservationBid()) if self.profile.getReservationBid() is not None else 0
        opponent_bid_util = self.profile.getUtility(bid)

        if our_reservation_util > opponent_bid_util:
            return False
        # calculate the starting time (in range [0,1]) of the window of bids
        r = Decimal(1.0) - Decimal(progress)
        start = Decimal(progress) - r

        # calulate the lowest utility offered in previous bids
        min_opponent_bid_util = self._calc_min_w(start)

        # First Equation: Acceptance probability
        p_accept = 1.0 if opponent_bid_util >= min_opponent_bid_util else 1 - (min_opponent_bid_util - opponent_bid_util)

        # Generate random rValue
        r_value = random.uniform(0, 1)

        # Time-based delta adjustment
        delta = min_val + (max_val - min_val) * ((1.0 - progress)**epsilon)
        r_value += delta

        # Statistical condition
        if (p_accept - r_value) >= rvalue_threshold:
            return True

        # AC_Next(1.02) condition
        if opponent_bid_util >= our_next_util * Decimal(alpha): # 2% more than what we want increase
            return True

        if progress + self.max_time_for_turn > 1:
            return True

        return False

    def find_bid(self) -> Bid:
        # compose a list of all possible bids
        lower_window = 0.9

        # Filter all bids based on
        possible_bids = dict()
        for bid in self.all_bids_utility:
            if self.all_bids_utility.get(bid) >= lower_window:
                possible_bids[bid] = Decimal(str(self.opponent_model.get_predicted_utility(bid))) + self.all_bids_utility.get(bid)

        sorted_bids = sorted(possible_bids.items(), key=lambda x: x[1], reverse=True)
        index = randint(0, round(len(sorted_bids) * 0.1))
        return sorted_bids[index][0]

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
