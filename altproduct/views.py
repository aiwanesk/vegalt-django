""" Views file """

import requests
import random
import json

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse

from .forms import RegisterForm, SearchForm
from .models import Product, Category, FavouriteProduct


def index(request):
    """ Home route. """

    context = {
        'h1_tag': 'Du gras oui, mais de qualité !',
        'search_form': SearchForm(),
    }
    return render(request, 'altproduct/index.html', context)


def legal(request):
    """ Legal route. """

    context = {
        'h1_tag': 'Mentions légales',
        'search_form': SearchForm(),
    }
    return render(request, 'altproduct/legal.html', context)


def register(request):
    """ Account creation route. """

    context = {
        'h1_tag': 'Créer un compte',
        'h2_tag': 'Un nom, un mot de passe et c\'est parti !',
        'search_form': SearchForm(),
        }

    # If the register form is posted
    if request.method == "POST":

        register_form = RegisterForm(request.POST)

        # Verify all datas posted
        if register_form.is_valid():
            username = register_form.cleaned_data['username']
            email = register_form.cleaned_data['email']
            password = register_form.cleaned_data['password']

            # Create the new user in database if it's not existing
            user = User.objects.filter(email=email)
            if not user.exists():
                user = User.objects.create_user(username, email=email, password=password)

                return redirect('altproduct:account_login')

        else:
            context['errors'] = register_form.errors.items()

    # If not, create the empty register form
    else:
        register_form = RegisterForm()

    context['register_form'] = register_form

    return render(request, 'altproduct/account.html', context)


class CustomLoginView(LoginView):
    """ Subclass from Django LoginView. Personnalized account login route. """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'h1_tag': 'Connexion à votre compte',
            'h2_tag': 'Entrez vos identifiants de connexion pour accéder à votre compte',
            'search_form': SearchForm(),
            'next': reverse_lazy('altproduct:account')
        })

        return context


def account(request):
    """ Account route """

    context = {
        'h1_tag': 'Ahoy',
        'h2_tag': 'Paramètres de votre compte',
        'search_form': SearchForm(),
    }

    return render(request, 'altproduct/account.html', context)


def alternative(request):
    """ Alternative route, when a product is searched """

    searched_product = request.GET.get('produit')
    user = request.user

    context = {
        'h1_tag': searched_product,
        'search_form': SearchForm(),
        'searched_product': searched_product,
    }

    try:
        category = Category.objects.get(name__icontains=searched_product, alternative=False)
        product = Product.objects.filter(category_id=category.id).order_by('?')[1]

        context['searched_product_img'] = product.image
        context['h2_tag'] = 'Vous pouvez remplacer cet aliment par :'

        categories = Category.objects.filter(name__icontains=searched_product, alternative=True)

        # Isolate products registered by the user
        if user:
            fav_products = FavouriteProduct.objects.filter(user_id=user.id)
            fav_products_id = [fav_product.product_id for fav_product in fav_products]

        products = []
        for category in categories:
            # Get all products by category, excluding products registered
            products_per_category = Product.objects.filter(category_id=category.id).exclude(id__in=fav_products_id)

            for product in products_per_category:
                # Keep FR products
                if product not in products and not 'Hamburguesa' in product.name and not 'Bebida' in product.name:
                    products.append(product)

        if not products:
            context['h2_tag'] = 'Aucun produit alternatif n\'a été trouvé :('
            context['message'] = 'Essayez une nouvelle recherche avec un autre produit.'

        else:
            paginator = Paginator(products, 9)
            page = request.GET.get('page')
            alt_products = paginator.get_page(page)

            context['alt_products'] = alt_products
            context['paginate'] = True

    except Category.DoesNotExist:
        context['h2_tag'] = 'Votre recherche n\'a retourné aucun résultat'
        context['message'] = 'Essayez une nouvelle recherche avec un autre produit.'

    return render(request, 'altproduct/alternative.html', context)


def product_detail(request, product_id, product_name):
    """ Product detail route. """

    # Get product by id, because many products can have the same name
    product = Product.objects.get(id=product_id)

    context = {
        'h1_tag': product_name,
        'h2_tag': 'Informations nutritionnelles',
        'search_form': SearchForm(),
        'product': product,
        'searched_product_img': product.image,
    }

    return render(request, 'altproduct/product.html', context)


def save_product(request):
    """ Route to get save product Ajax script. Return confirmation or error message. """

    response_data = {}

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        product_id = request.POST.get('product_id')

        fav_product_for_current_user = FavouriteProduct.objects.filter(product_id=product_id, user_id=user_id)
        if not fav_product_for_current_user.exists():
            FavouriteProduct.objects.create(product_id=product_id, user_id=user_id)
            response_data['success_message'] = 'Produit sauvegardé'
        else:
            response_data['error_message'] = 'Produit déjà sauvegardé'

    else:
        response_data['error_message'] = 'Impossible de sauvegarder le produit'

    return HttpResponse(
        json.dumps(response_data),
        content_type='application/json',
    )


def fav_products(request):
    """ Favourite products page. Need an account to have access to it. """

    context = {
        'h1_tag': 'Les alternatives gardées au chaud',
        'search_form': SearchForm(),
    }

    user = request.user
    fav_products = FavouriteProduct.objects.filter(user_id=user.id)

    if fav_products.exists():
        products = []
        for fav_product in fav_products:
            product = Product.objects.get(id=fav_product.product_id)
            if product not in products:
                products.append(product)

        paginator = Paginator(products, 9)
        page = request.GET.get('page')
        alt_products = paginator.get_page(page)

        context['h2_tag'] = 'Très bon choix :)'
        context['alt_products'] = alt_products
        context['paginate'] = True

    else:
        context['h2_tag'] = 'Pas de produit enregistré pour le moment'
        context['message'] = 'Faites vite une recherche !'

    return render(request, 'altproduct/alternative.html', context)
