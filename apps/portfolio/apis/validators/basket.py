"""
basket.py

This module defines the serializers for validating input parameters for the
Basket-related API endpoints. It utilizes Django REST Framework's serializers
to ensure that the data provided for creating a basket meets the necessary 
validation criteria.
"""

from rest_framework import serializers

from apps.portfolio.constants import BasketStates, BasketTypes, ProductTypes, BrokerEnum


class CreateBasketParamsValidator(serializers.Serializer):
    """
    Serializer for validating the parameters required to create a new basket.

    Attributes:
        user_id (str): The unique identifier for the user who owns the basket.
        model_id (str): The identifier for the model associated with the basket.
        basket_type (str): The type of basket, selected from predefined choices.
        product_type (str): The type of product associated with the basket, selected from predefined choices.
        payment_id (str): The identifier for the payment associated with the basket.
        recommendation_id (int): The identifier for the recommendation from the catalogue.
        user_allocation (dict, optional): A JSON object containing allocation details for the user.
        cash_ingested (float, optional): The amount of cash ingested for the basket, if applicable.
        amount (float, optional): The amount associated with the basket creation.
        profit_target (float, optional): The percentage target for profit.
        profit_target_value (float, optional): The specific profit target value.

    Validations:
        - All required fields (`user_id`, `model_id`, `basket_type`, `product_type`, `payment_id`, `recommendation_id`) must be provided.
        - `recommendation_id` must be an integer.
        - `basket_type` and `product_type` must be selected from predefined choices.
        - Optional fields (`user_allocation`, `cash_ingested`, `amount`, `profit_target`, `profit_target_value`)
          can be provided based on the basket creation process.
    """

    user_id = serializers.CharField(required=True)
    model_id = serializers.CharField(required=True)
    broker = serializers.ChoiceField(choices=BrokerEnum.CHOICES.value, required=False, allow_null=True, allow_blank=True)
    basket_type = serializers.ChoiceField(choices=BasketTypes.CHOICES.value, required=True)
    product_type = serializers.ChoiceField(choices=ProductTypes.CHOICES.value,required=True)
    payment_id = serializers.CharField(required=True)
    recommendation_id = serializers.IntegerField(required=True)
    user_allocation = serializers.JSONField(required=False)
    cash_ingested = serializers.FloatField(required=False)
    amount = serializers.FloatField(required=False)
    end_amount = serializers.FloatField(required=False)
    profit_target_1 = serializers.FloatField(required=False, allow_null=True)
    profit_target_2 = serializers.FloatField(required=False, allow_null=True)
    profit_target_1_value = serializers.FloatField(required=False)
    profit_target_2_value = serializers.FloatField(required=False)


class BasketQueryParamsValidator(serializers.Serializer):
    """
    Validates the query parameters for fetching basket details.

    Fields:
        user_id (str): The ID of the user (required).
        current_state (str): The current state of the basket, selected from predefined choices.
    """
    user_id = serializers.CharField(required=True)
    current_state = serializers.ChoiceField(choices=BasketStates.CHOICES.value)
    broker = serializers.ChoiceField(choices=BrokerEnum.CHOICES.value, required=False, allow_null=True, allow_blank=True)



class UpdateBasketFieldsValidator(serializers.Serializer):
    """
    Validates the fields for updating a basket. All fields are optional, allowing for partial updates.

    Fields:
        id (int): The ID of the basket (optional).
        user_id (str): The ID of the user (optional).
        model_id (str): The ID of the model (optional).
        basket_type (str): The type of basket, selected from predefined choices (optional).
        product_type (str): The type of product associated with the basket, selected from predefined choices (optional).
        payment_id (str): The ID of the payment (optional).
        recommendation_id (int): The recommendation ID (optional).
        user_allocation (dict): The user's allocation in JSON format (optional).
        cash_ingested (float): The amount of cash ingested (optional).
        amount (float): The amount to be updated (optional).
        profit_target (float): The profit target (optional).
        profit_target_value (float): The value of the profit target (optional).
    """
    id = serializers.IntegerField(required=False)
    user_id = serializers.CharField(required=False)
    model_id = serializers.CharField(required=False)
    broker = serializers.ChoiceField(choices=BrokerEnum.CHOICES.value, required=False, allow_null=True, allow_blank=True)
    basket_type = serializers.ChoiceField(choices=BasketTypes.CHOICES.value, required=False)
    product_type = serializers.ChoiceField(choices=ProductTypes.CHOICES.value,required=False)
    payment_id = serializers.CharField(required=False)
    recommendation_id = serializers.IntegerField(required=False)
    user_allocation = serializers.JSONField(required=False)
    cash_ingested = serializers.FloatField(required=False)
    amount = serializers.FloatField(required=False)
    end_amount = serializers.FloatField(required=False)
    profit_target_1 = serializers.FloatField(required=False)
    profit_target_1_value = serializers.FloatField(required=False)
    profit_target_2 = serializers.FloatField(required=False)
    profit_target_2_value = serializers.FloatField(required=False)


class BasketDetailsRequestValidator(serializers.Serializer):
    """
    Serializer to validate the request data for fetching basket details.

    Fields:
        basket_id (int): The ID of the basket to fetch details for. This field is required.
        recommendation_id (int): The ID of the recommendation associated with the basket. This field is required.
    """

    basket_id = serializers.IntegerField(required=True)
    recommendation_id = serializers.IntegerField(required=True)
