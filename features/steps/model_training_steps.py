from behave import *


@given("a dataset of georeferenced {parcel} geometries within the {city}")
def step_impl(context, parcel, city):
	context.city = city
	context.layer = parcel

	pass


@step("the dataset includes a valid series of explanatory and {dependent} spatial or quantitative variables")
def step_impl(context, dependent):
	context.dependent = dependent

	pass


@when("{train_size}% of the available data is used to train a RandomForestRegressor model")
def step_impl(context, train_size):
	raise NotImplementedError()


@then("use the remaining data to test the accuracy of my trained model")
def step_impl(context):
	raise NotImplementedError()


@step("extract the most significant spatial predictors of the {dependent} variables")
def step_impl(context, dependent):
	raise NotImplementedError()
