from collections import defaultdict
from typing import Dict, List

from geniusweb.issuevalue.Bid import Bid
from geniusweb.issuevalue.DiscreteValueSet import DiscreteValueSet
from geniusweb.issuevalue.Domain import Domain
from geniusweb.issuevalue.Value import Value


class OpponentModel:
    def __init__(self, domain: Domain):
        self.offers = []
        self.domain = domain

        self.issue_estimators = {
            i: IssueEstimator(v) for i, v in domain.getIssuesValues().items()
        }

    def update(self, bid: Bid):
        # keep track of all bids received
        self.offers.append(bid)

        # update all issue estimators with the value that is offered for that issue
        for issue_id, issue_estimator in self.issue_estimators.items():
            issue_estimator.update(bid.getValue(issue_id))

    def get_predicted_utility(self, bid: Bid):
        if len(self.offers) == 0 or bid is None:
            return 0

        # initiate
        total_issue_weight = 0.0
        value_utilities = []
        issue_weights = []

        for issue_id, issue_estimator in self.issue_estimators.items():
            # get the value that is set for this issue in the bid
            value: Value = bid.getValue(issue_id)

            # collect both the predicted weight for the issue and
            # predicted utility of the value within this issue
            value_utilities.append(issue_estimator.get_value_utility(value))
            issue_weights.append(issue_estimator.weight)

            total_issue_weight += issue_estimator.weight

        # normalise the issue weights such that the sum is 1.0
        if total_issue_weight == 0.0:
            issue_weights = [1 / len(issue_weights) for _ in issue_weights]
        else:
            issue_weights = [iw / total_issue_weight for iw in issue_weights]

        # calculate predicted utility by multiplying all value utilities with their issue weight
        predicted_utility = sum(
            [iw * vu for iw, vu in zip(issue_weights, value_utilities)]
        )

        return predicted_utility
    
    def calculate_concessions(self) -> List[float]:
        if len(self.offers) < 2:
            return None  # Not enough data to compare
        
        # Calculates estimated utility value given current estimated utilities and then calculates the differences between every index t and t+1
        estimated_utilities = [self.get_predicted_utility(bid) for bid in self.offers] 
        estimated_utility_difference = [t - t1 for t, t1 in zip(estimated_utilities, estimated_utilities[1:])]

        return estimated_utility_difference

    def get_issue_weights(self) -> Dict[Value, float]:
        weights_dict = {}
        for issue_id, issue_estimator in self.issue_estimators.items():
            weights_dict[issue_id] = issue_estimator.weight

        return weights_dict

    def get_issue_value_utilities(self, issue_id: str) -> Dict[Value, float]:
        if issue_id not in self.issue_estimators:
            raise ValueError(f"Issue ID '{issue_id}' not found in opponent model.")

        issue_estimator = self.issue_estimators[issue_id]
        possible_values = issue_estimator.value_trackers.keys()
        # Returns a dictionary with estimated utilities for each value
        return {value: issue_estimator.get_value_utility(value) for value in possible_values}

    def percent_below_zero(self, util_diff: List[float]) -> float:
        return len([x for x in util_diff if x < 0]) / len(util_diff)

class IssueEstimator:
    def __init__(self, value_set: DiscreteValueSet):
        if not isinstance(value_set, DiscreteValueSet):
            raise TypeError(
                "This issue estimator only supports issues with discrete values"
            )

        self.bids_received = 0
        self.max_value_count = 0
        self.num_values = value_set.size()
        self.value_trackers = defaultdict(ValueEstimator)
        self.weight = 0

    def update(self, value: Value):
        self.bids_received += 1

        # get the value tracker of the value that is offered
        value_tracker = self.value_trackers[value]

        # register that this value was offered
        value_tracker.update()

        # update the count of the most common offered value
        self.max_value_count = max([value_tracker.count, self.max_value_count])

        # update predicted issue weight
        # the intuition here is that if the values of the receiverd offers spread out over all
        # possible values, then this issue is likely not important to the opponent (weight == 0.0).
        # If all received offers proposed the same value for this issue,
        # then the predicted issue weight == 1.0
        equal_shares = self.bids_received / self.num_values
        self.weight = (self.max_value_count - equal_shares) / (
            self.bids_received - equal_shares
        )

        # recalculate all value utilities
        for value_tracker in self.value_trackers.values():
            value_tracker.recalculate_utility(self.max_value_count, self.weight)

    def get_value_utility(self, value: Value):
        if value in self.value_trackers:
            return self.value_trackers[value].utility

        return 0


# this class tracks how often a specific value has been offered and tracks its utility
class ValueEstimator:
    def __init__(self):
        self.count = 0
        self.utility = 0

    def update(self):
        self.count += 1

    def recalculate_utility(self, max_value_count: int, weight: float):
        if weight < 1:
            mod_value_count = ((self.count + 1) ** (1 - weight)) - 1
            mod_max_value_count = ((max_value_count + 1) ** (1 - weight)) - 1

            self.utility = mod_value_count / mod_max_value_count
        else:
            self.utility = 1
