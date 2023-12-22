import base64

from django.contrib.auth.hashers import make_password
from django.core import validators
from django.core.files.base import ContentFile
from rest_framework import serializers

from api.functions import adding_ingredients
from recipes.models import (
    Ingredient,
    Tag,
    Recipe,
    RecipeIngredient,
    Follow,
    FavoriteRecipe,
    ShoppingCart
)
from users.models import User

COOKING_TIME_ANF_AMOUNT_MIN = 1
COOKING_TIME_ANF_AMOUNT_MAX = 32000
USERNAME_MAX_LENGTH = 150
EMAIL_MAX_LENGTH = 254


class Base64ImageField(serializers.ImageField):
    """Сериализатор изображений."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор работы с пользователями."""
    id = serializers.IntegerField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        try:
            user = self.context['request'].user
        except KeyError:
            return False
        if user.is_anonymous:
            return False
        return obj.following.filter(user=user).exists()


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания пользователя."""
    username = serializers.CharField(
        max_length=USERNAME_MAX_LENGTH,
        required=True,
        validators=(
            validators.MaxLengthValidator(USERNAME_MAX_LENGTH),
            validators.RegexValidator(r'^[\w.@+-]+\Z')
        )
    )
    email = serializers.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        required=True
    )
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
            'is_subscribed'
        )

    def validate(self, attrs):
        user = User.objects.filter(email=attrs.get('email'))
        if user:
            user = user.first()
            if user.username != attrs.get('username'):
                raise serializers.ValidationError(
                    {'E-mail не уникален'}
                )
        user = User.objects.filter(username=attrs.get('username')).first()
        if user:
            if user.email != attrs.get('email'):
                raise serializers.ValidationError(
                    {'Имя не уникально'}
                )
        if attrs.get('password'):
            attrs['password'] = make_password(attrs['password'])
        return super().validate(attrs)

    def get_is_subscribed(self, obj):
        return False


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug'
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта & ингредиента."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор списка/одного рецептов, удаления."""
    tags = TagSerializer(many=True)
    image = Base64ImageField(
        required=True,
        allow_null=False
    )
    author = UserSerializer()
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return obj.is_in_shopping_cart(user)

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return obj.is_favorited(user)


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания/обновления ингредиентов."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        min_value=COOKING_TIME_ANF_AMOUNT_MIN,
        max_value=COOKING_TIME_ANF_AMOUNT_MAX
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount'
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания/обновления рецептов."""
    image = Base64ImageField(
        required=True,
        allow_null=False
    )
    ingredients = RecipeIngredientCreateSerializer(many=True)
    cooking_time = serializers.IntegerField(
        min_value=COOKING_TIME_ANF_AMOUNT_MIN,
        max_value=COOKING_TIME_ANF_AMOUNT_MAX
    )

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        adding_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        new_tags = validated_data.pop('tags')
        new_ingredients = validated_data.pop('ingredients')
        instance.tags.set(new_tags)
        RecipeIngredient.objects.filter(recipe=instance).delete()
        adding_ingredients(new_ingredients, instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    following = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all()
    )

    class Meta:
        model = Follow
        fields = '__all__'
        read_only_fields = ('user',)


class CheckFollowSerializer(serializers.ModelSerializer):
    """Сериализация подписчиков."""

    class Meta:
        model = Follow
        fields = ('user', 'following')

    def validate(self, obj):
        request_method = self.context.get('request').method
        user, following = obj['user'], obj['following']
        follow = user.follows.filter(following=following).exists()
        if request_method == 'POST':
            if user == following:
                raise serializers.ValidationError('Подписка на самого себя')
            if follow:
                raise serializers.ValidationError('Вы уже подписаны')
        if request_method == 'DELETE':
            if user == following:
                raise serializers.ValidationError('Ошибка')
            if not follow:
                raise serializers.ValidationError({'errors': 'Ошибка'})
        return obj


class RecipeShortSerializer(serializers.ModelSerializer):
    image = Base64ImageField(
        required=True,
        allow_null=False,
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class AuthorSerializer(serializers.ModelSerializer):
    """Сериализатор подписки на автора."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'email',
            'id',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        ]

    def get_recipes_count(self, obj):
        return obj.recipes_count

    def get_recipes(self, obj):
        recipes = obj.get_user_recipes
        return RecipeShortSerializer(recipes, many=True).data

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return obj.following.filter(user=user).exists()


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = FavoriteRecipe
        fields = (
            'user',
            'recipe'
        )

    def validate(self, attrs):
        user = self.context['request'].user
        recipe = attrs['recipe']
        if user.favorite_recipes.filter(recipe=recipe).exists():
            raise serializers.ValidationError('Уже в избранном')
        return attrs


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = (
            'user',
            'recipe'
        )

    def validate(self, attrs):
        user = self.context['request'].user
        recipe = attrs['recipe']
        if user.cart_recipes.filter(recipe=recipe).exists():
            raise serializers.ValidationError('Уже в корзине')
        return attrs
