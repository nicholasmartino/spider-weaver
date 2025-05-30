import os
import pickle
from dataclasses import dataclass
from math import sqrt
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import PartialDependenceDisplay, permutation_importance
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


@dataclass
class Predictor:
    data: pd.DataFrame
    regressor: RandomForestRegressor
    predictors: List[str]
    predicted: str
    test_size: float
    random_state: int
    percentile: int
    
    def __init__(self, data=None, predictors=None, predicted=None, test_size=0.2, random_state=1, percentile=99):
        assert predicted in data.columns, AssertionError(f"Column {predicted} not found in input data")

        # Calculate and filter head and tails
        data = data.loc[:, ~data.columns.duplicated()]
        p_low = np.percentile(data[predicted], 100 - percentile)
        p_high = np.percentile(data[predicted], percentile)
        data = data.loc[(data[predicted] > p_low) & (data[predicted] < p_high)]

        self.data = data
        self.predictors = predictors
        self.predicted = predicted
        self.random_state = random_state
        self.regressor = None
        self.test_size = test_size
        self.importance = pd.DataFrame()
        self.permutation = None
        return

    def split(self):
        return train_test_split(self.data.loc[:, self.predictors], self.data[self.predicted],
                                test_size=self.test_size, random_state=self.random_state, shuffle=False)

    def train(self):
        x_train, x_test, y_train, y_test = self.split()
        rfr = RandomForestRegressor(random_state=self.random_state, n_estimators=90, n_jobs=-1)
        rfr.fit(x_train, y_train)
        return rfr

    def test(self, plot_dir):
        self._is_regressor_null()
        x_train, x_test, y_train, y_test = self.split()
        
        # Filter out rows with missing values to ensure consistent sample counts
        valid_indices = x_test.loc[:, self.predictors].dropna().index
        x_test_clean = x_test.loc[valid_indices, self.predictors]
        y_test_clean = y_test.loc[valid_indices]
        
        y_pred = self.regressor.predict(x_test_clean)

        if not os.path.exists(plot_dir):
            os.makedirs(plot_dir)

        mean_error = round(sqrt(mean_squared_error(y_test_clean, y_pred)), 2)
        r2 = round(r2_score(y_test_clean, y_pred), 2)
        joint = sns.jointplot(x=y_pred, y=y_test_clean, kind="reg", scatter_kws={'alpha': 0.1}, seed=0)
        joint.ax_joint.annotate(f'rmse: {mean_error} | r2: {r2}', xy=(0.05, 0.95), xycoords='axes fraction')
        joint.ax_joint.set_xlabel(f'{self.predicted} (predicted data)')
        joint.ax_joint.set_ylabel(f'{self.predicted} (test set)')
        joint.savefig(f'{plot_dir}/prediction_{self.predicted}.png', transparent=True)
        return self

    def predict(self, x):
        # Filter to only include rows without missing values in predictor columns
        x_clean = x.loc[:, self.predictors].dropna()
        return self.regressor.predict(x_clean)

    def save(self, directory):
        self._is_regressor_null()

        if not os.path.exists(directory):
            os.makedirs(directory)

        return pickle.dump(self, open(f'{directory}/predictor-{self.predicted}.pkl', 'wb'))

    def _is_regressor_null(self):
        assert self.regressor is not None, AssertionError("Regressor not found")

    def get_permutation_importance(self):
        if self.permutation is not None:
            return self.permutation.sort_values(by='dependencies', ascending=False)
        x_train, x_test, y_train, y_test = self.split()
        perm_imp = permutation_importance(
            estimator=self.regressor,
            X=x_train,
            y=y_train,
            random_state=self.random_state
        )
        self.permutation = pd.DataFrame({
            'feature': self.predictors,
            'dependencies': pd.Series(perm_imp['importances_mean'])
        }).sort_values(by='dependencies', ascending=False)
        return self.permutation

    def plot_partial_dependence(self, plot_dir, features):
        x_train, x_test, y_train, y_test = self.split()

        # Plot dependencies
        _, axes = plt.subplots(nrows=2, ncols=3, figsize=(10, 6))
        dependence_display = PartialDependenceDisplay.from_estimator(self.regressor, x_train, features, ax=axes.ravel(), kind='average')
        plt.tight_layout()

        plot_path = f'{plot_dir}/partial_dependencies_{self.predicted}.png'
        dependence_display.figure_.savefig(plot_path, dpi=150, transparent=True)
        return set(features)


def load_pickle(path):
    with open(path, "rb") as file:
        return pickle.load(file)
