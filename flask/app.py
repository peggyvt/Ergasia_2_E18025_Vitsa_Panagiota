from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from flask import Flask, request, jsonify, redirect, Response
import json
import uuid
import time
import os, sys
sys.path.append('./data')

#connect to our local MongoDB
mongodb_hostname = os.environ.get("MONGO_HOSTNAME","localhost")
client = MongoClient('mongodb://'+mongodb_hostname+':27017/')

#choose database
db = client['DSMarkets']

#choose collections
users = db['Users']
products = db['Products']

#initiate flask app
app = Flask(__name__)
users_sessions = {}

#####################################
########## BASIC FUNCTIONS ##########
#####################################

#create session for the user
def create_session(name):
    user_uuid = str(uuid.uuid1())
    users_sessions[user_uuid] = (name, time.time())
    return user_uuid  

#check user's session validity
def is_session_valid(user_uuid):
    return user_uuid in users_sessions

#get all users from User collection
@app.route('/getallusers', methods=['GET'])
def get_all_users():
    iterable = users.find({})
    output = []
    for user in iterable:
        user['_id'] = None
        output.append(user)
    return jsonify(output)

#get all products from Products collection
@app.route('/getallproducts', methods=['GET'])
def get_all_products():
    iterable = products.find({})
    output = []
    for product in iterable:
        product['_id'] = None
        output.append(product)
    return jsonify(output)

#create admin
@app.route('/createAdmin', methods=['POST'])
def create_admin():
    #request JSON data message
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("Bad json content.", status=500, mimetype='application/json')
    if data == None:
        return Response("Bad request.", status=500, mimetype='application/json')
    if not "name" in data or not "password" or not "email" in data:
        return Response("Information incomplete.", status=500, mimetype="application/json")

    #if admin doesn't exist in the database
    if users.find({"email":data["email"]}).count()== 0:
        
        #then store their data in a dictionary 'admin'
        admin = {"name": data['name'], "password":data['password'], "email":['email']}
        
        #update data with category admin status
        data.update({'category':'admin'})

        #insert the data in 'Users' collection
        users.insert_one(data)

        #successful message
        return Response(data['name'] + " was added to the MongoDB!", status=200, mimetype='application/json')
    else:
        #error message - admin already exists
        return Response("An admin with the given email already exists.", status=401, mimetype='application/json')

#create user
@app.route('/createUser', methods=['POST'])
def create_user():
    #request JSON data message
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("Bad json content.", status=500, mimetype='application/json')
    if data == None:
        return Response("Bad request.", status=500, mimetype='application/json')
    if not "name" in data or not "password" or not "email" in data:
        return Response("Information incomplete.", status=500, mimetype="application/json")

    #if user doesn't exist in the database
    if users.find({"email":data["email"]}).count() == 0:
        
        #then store their data in a dictionary 'user'
        user = {"name": data['name'], "email":['email'], "password":data['password']}
        
        #update data with category user status
        data.update({'category':'user'})

        #update data with empty basket
        tp = 0
        data.update({'basket':[{'total_price':tp}]})

        #update data with empty history of user's orders
        data.update({'historyOrders':[]})

        #insert the data in 'Users' collection
        users.insert_one(data)

        #successful message
        return Response(data['name'] + " was added to the MongoDB!", status=200, mimetype='application/json')
    else:
        #error message - user already exists
        return Response("A user with the given email already exists.", status=401, mimetype='application/json')

#######################################
########## ADMIN ENTRYPOINTS ##########
#######################################

@app.route('/insertProduct', methods=['UPDATE'])
def insert_product():
    #request JSON data message
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("Bad json content.", status=500, mimetype='application/json')
    if data == None:
        return Response("Bad request.", status=500, mimetype='application/json')
    if not "email" in data or not "id" in data or not "name" in data or not "category" or not "stock" in data or not "price" in data:
        return Response("Information incomplete.", status=500, mimetype="application/json")

    admin = users.find_one({"email":data['email']})
    if admin != None: #if user exists
        if admin['category'] == 'admin':
            #if product doesn't exist in the database
            if products.find({"id":data["id"]}).count() == 0:
                #then store the product in a dictionary 'product'
                if "description" in data: #description is an optional field
                    product = {"id": data['id'], "name": data['name'], "category":data['category'], "stock":data['stock'], "description":data['description'], "price":data['price']}
                else: #if the admin does not give product description
                    product = {"id": data['id'], "name": data['name'], "category":data['category'], "stock":data['stock'], "price":data['price']}
                #insert the data in 'Products' collection
                products.insert_one(product)

                #successful message
                return Response(data['name'] + " was added to the collection Products!", status=200, mimetype='application/json')
            else:
                #error message - user already exists
                return Response("This product already exists.", status=401, mimetype='application/json')
        else: 
            return Response("Only admin allowed to execute this.") #not an admin category
    else:
        return Response("There isn't an admin with that email.") #admin does not exist

#delete product
@app.route('/deleteProduct', methods=['DELETE'])
def delete_product():
    #request JSON data message
    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("Bad json content.", status=500, mimetype='application/json')
    if data == None:
        return Response("Bad request.", status=500, mimetype='application/json')
    if not "id" in data or not "email" in data:
        return Response("Information incomplete.", status=500, mimetype="application/json")

    admin = users.find_one({"email":data['email']})
    if admin != None: #if user exists
        if admin['category'] == 'admin':
            product = products.find_one({"id":data["id"]}) #find product by id
            if product != None: #if product exists, delete it
                products.delete_one(product) #delete
                product_name = product["name"] #insert in var the name of the product in order to print it later
                msg = product_name + " was deleted." #delete verification message
                return Response(msg, status=200, mimetype='application/json') #successful message and status
            else: #if product doesn't exist, print corresponding message
                return Response("There is no product with that id.")
        else: 
            return Response("Only admin allowed to execute this.") #not an admin category
    else:
        return Response("There isn't an admin with that email.") #admin does not exist

#update product
@app.route('/updateProduct', methods=['UPDATE'])
def update_product():
    #request JSON data message
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("Bad json content.", status=500, mimetype='application/json')
    if data == None:
        return Response("Bad request.", status=500, mimetype='application/json')
    if not "id" in data or (not "name" in data and not "price" in data and not "description" in data and not "stock" in data) or not "email" in data:
        return Response("Information incomplete.", status=500, mimetype="application/json")

    admin = users.find_one({"email":data['email']})
    if admin != None: #if user exists
        if admin['category'] == 'admin':
            product = products.find_one({"id":data["id"]}) #find product by id
            if product != None: #if product exists, update the content
                #set the new values
                if "name" in data:
                    product = products.update_one({'id':data["id"]}, {'$set': {'name':data["name"]}}) #set the new name
                if "price" in data:
                    product = products.update_one({'id':data["id"]}, {'$set': {'price':data["price"]}}) #set the new price
                if "description" in data:
                    product = products.update_one({'id':data["id"]}, {'$set': {'description':data["description"]}}) #set the new description
                if "stock" in data:
                    product = products.update_one({'id':data["id"]}, {'$set': {'stock':data["stock"]}}) #set the new stock
                msg = "Updated successfully"
                return Response(msg, status=200, mimetype='application/json')
            else: #if product doesn't exist, print corresponding message
                return Response("There is no product with that id.", status=500, mimetype='application/json')
        else: 
            return Response("Only admin allowed to execute this.") #not an admin category
    else:
        return Response("There isn't an admin with that email.") #admin does not exist

######################################
########## USER ENTRYPOINTS ##########
######################################

#login
@app.route('/login', methods=['POST'])
def login():
    #request JSON data message
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("Bad json content.", status=500, mimetype='application/json')
    if data == None:
        return Response("Bad request.", status=500, mimetype='application/json')
    if not "name" in data or not "password" in data or not "email" in data:
        return Response("Information incomplete.", status=500, mimetype="application/json")

    #if user exists 
    user = users.find_one({"email":data['email']})
    if user != None: #if user exists
        if user['category'] == 'user': #if user is not an admin
            if users.find_one( {"$and": [ {"name":data['name']}, {"password":data['password']}] } ):
                user_uuid = create_session(data['name']) #create user session
                res = {"uuid": user_uuid, "name": data['name']} #assign data in res variable in order to print them later
                return Response("Authentication successful. User data: " + json.dumps(res), mimetype='application/json', status=200) #successful message
            else: #unsuccessful login - status error
                return Response("Wrong username or password.", status=400, mimetype='application/json')
        else: 
            return Response("Admins cannot login - You have to be a user.")
    else:
        return Response("There isn't a user with that email.")

#user searches products
@app.route('/getProducts', methods=['GET'])
def get_products():
    #request JSON data message
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("Bad json content.", status=500, mimetype='application/json')
    if data == None:
        return Response("Bad request.", status=500, mimetype='application/json')
    if not "name" in data and not "category" in data and not "id" in data and not "email" in data:
        return Response("Information incomplete.", status=500, mimetype="application/json")

    if ("name" in data and "category" in data) or ("name" in data and "id" in data) or ("category" in data and "id" in data) or ("name" in data and "category" in data and "id" in data):
        return Response("Information incomplete.", status=500, mimetype="application/json")
    elif "email" not in data:
        return Response("Information incomplete.", status=500, mimetype="application/json")

    uuid = request.headers.get('Authorization') #get uuid from user
    if is_session_valid(uuid) : #if uuid is valid, then execute the entrypoint
        user = users.find_one({"email":data['email']})
        if user != None: #if user exists
            if user['category'] == 'user': #if user is not an admin
                a = 0
                product_list = []
                if "name" in data: #product based on name
                    products1 = products.find({"name":data['name']})
                    if products1 != 0: #product exists
                        for product in products1:
                            product['_id'] = None
                            product_list.append(product) #add each product to the list
                            a = 1
                    
                    if len(product_list) == 0: #product does not exist
                        return Response("There are no products with that name.")
                elif "category" in data: #product based on category
                    products1 = products.find({"category":data['category']})
                    if products1 != None: #product exists
                        for product in products1:
                            product['_id'] = None
                            product_list.append(product) #add each product to the list
                            a = 1
                        for i in range(len(product_list)): #ascending order with bubblesort
                            for j in range(0, len(product_list)-i-1):
                                if product_list[j].get("price") > product_list[j+1].get("price"):
                                    temp = product_list[j]
                                    product_list[j] = product_list[j+1]
                                    product_list[j+1] = temp

                    if len(product_list) == 0: #product does not exist
                        return Response("There are no products in this category.")
                elif "id" in data: #product based on id
                    products1 = products.find({"id":data['id']})
                    if products1 != 0: #product exists
                        for product in products1:
                            product['_id'] = None
                            product_list.append(product) #add each product to the list
                            a = 1

                    if len(product_list) == 0: #product does not exist
                        return Response("There is no product with that id.")

                if a == 1: #if one of the three existed, then print the products' list
                    return Response(json.dumps(product_list, indent=4), status=200, mimetype='application/json')
            else: #if user is an admin
                return Response("Admin cannot get products - Login as a user.\n")
        else: #user does not exist
            return Response("There isn't a user with that email.")
    else:  #user not authenticated
        return Response("User has not been authenticated.", status=401, mimetype='application/json')

#user adds product to basket
@app.route('/addProductToBasket', methods=['UPDATE'])
def add_product_to_basket():
    #request JSON data message
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("Bad json content.", status=500, mimetype='application/json')
    if data == None:
        return Response("Bad request.", status=500, mimetype='application/json')
    if not "id" in data or not "email" in data or not "quantity" in data:
        return Response("Information incomplete.", status=500, mimetype="application/json")

    uuid = request.headers.get('Authorization') #get uuid from user
    if is_session_valid(uuid) : #if uuid is valid, then execute the entrypoint
        user = users.find_one({"email":data['email']})
        if user != None: #if user exists
            if user['category'] == 'user': #if user is not an admin
                product = products.find_one({"id":data['id']}) #find the product in the 'Products' collection

                if product != None: #if product exists
                    if int(data["quantity"]) <= int(product["stock"]): #check if stock has enough items
                        cart = user["basket"] #local cart
                        cart.append({'id':data["id"], 'quantity':data["quantity"]}) #add the product

                        tp = user['basket'][0].get('total_price') + float(data["quantity"])*float(product["price"])
                        cart[0] = {'total_price':tp} #calculate the new total price of the basket after adding the product's price

                        user = users.update_one( {'email':data["email"]}, 
                                                {"$set": 
                                                        {"basket":cart} #set to the collection's basket the local one     
                                                }
                                            )

                        #successful message
                        return Response("Product was added successfully! \nCart: " + json.dumps(cart, indent = 4))
                    else: #stock not enough
                        return Response("The requested quantity is exceeding the product's stock.")
                else: #print error message
                   return Response("There is no product with that id.")
            else: #if user is an admin
                return Response("Admin cannot add products to basket - Login as a user.\n")
        else: #user does not exist
            return Response("There isn't a user with that email.")
    else:  #user not authenticated
        return Response("User has not been authenticated.", status=401, mimetype='application/json')

#print basket
@app.route('/printBasket', methods=['GET'])
def print_basket():
    #request JSON data message
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("Bad json content.", status=500, mimetype='application/json')
    if data == None:
        return Response("Bad request.", status=500, mimetype='application/json')
    if not "email" in data:
        return Response("Information incomplete.", status=500, mimetype="application/json")

    uuid = request.headers.get('Authorization') #get uuid from user
    if is_session_valid(uuid) : #if uuid is valid, then execute the entrypoint
        user = users.find_one({"email":data['email']})
        if user != None: #if user exists
            if user['category'] == 'user': #if user is not an admin
                return Response("Cart: " + json.dumps(user['basket'], indent = 4))
            else: #if user is an admin
                return Response("Admin cannot print basket - Login as a user.\n")
        else: #user does not exist
            return Response("There isn't a user with that email.")
    else: #user not authenticated
        return Response("User has not been authenticated.", status=401, mimetype='application/json')

#delete product from basket
@app.route('/deleteProductFromBasket', methods=['DELETE'])
def delete_product_from_basket():
    #request JSON data message
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("Bad json content.", status=500, mimetype='application/json')
    if data == None:
        return Response("Bad request.", status=500, mimetype='application/json')
    if not "id" in data or not "email" in data:
        return Response("Information incomplete.", status=500, mimetype="application/json")

    uuid = request.headers.get('Authorization') #get uuid from user
    if is_session_valid(uuid) : #if uuid is valid, then execute the entrypoint
        user = users.find_one({"email":data['email']})
        if user != None: #if user exists
            if user['category'] == 'user': #if user is not an admin
                productBasket = None
                k=-1
                product = products.find_one({"id":data['id']})

                if product != None:
                    for i in range (1, len(user['basket'])): #for each product in basket
                        id1 = user['basket'][i].get('id') #save the id
                        if id1 == data['id']: #if the id matches the user's data then the product exists
                            productBasket = user["basket"][i] #save the product in a variable
                            k = i #save the index of the product in a variable

                    if productBasket != None: #if the product the user wants to delete exists
                        basket1 = user["basket"] #create local basket to make changes and then set it to the collection

                        tp = user['basket'][0].get('total_price') - float(user["basket"][k]["quantity"])*float(product["price"]) #calculate the new total price after subtracting the product's price the user wants to delete 
                        basket1[0] = {'total_price':tp} #insert new total price to local basket

                        basket1.pop(k) #remove the product
                        
                        user = users.update_one( {'email':data["email"]}, 
                                                {"$set": 
                                                        {"basket":basket1} #set to the collection's basket the local one
                                                }
                                            )

                        product_name = product["name"] #insert in var the name of the product in order to print it later
                        msg = product_name + " was deleted." #delete verification message
                        return Response(msg, status=200, mimetype='application/json') #successful message and status
                    else: #product doesn't exist
                        return Response("The item does not belong in the basket.")
                else: #print error message
                    return Response("There is no product with that id.")
            else: #if user is an admin
                return Response("Admin cannot delete products from basket - Login as a user.\n")
        else:
            return Response("There isn't a user with that email.")
    else: #user not authenticated
        return Response("User has not been authenticated.", status=401, mimetype='application/json')

#user buys basket
@app.route('/buyBasket', methods=['UPDATE'])
def buy_basket():
    #request JSON data message
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("Bad json content.", status=500, mimetype='application/json')
    if data == None:
        return Response("Bad request.", status=500, mimetype='application/json')
    if not "email" in data or not "card_number" in data:
        return Response("Information incomplete.", status=500, mimetype="application/json")

    uuid = request.headers.get('Authorization') #get uuid from user
    if is_session_valid(uuid) : #if uuid is valid, then execute the entrypoint
        user = users.find_one({"email":data['email']})
        if user != None: #if user exists
            if user['category'] == 'user': #if user is not an admin
                if user != None and len(data['card_number'])==16:
                    cart = []
                    cart = user["basket"]

                    history = []
                    history = user["historyOrders"] #insert old history orders
                    history.append(cart) #insert the new order 

                    users.update_one( {'email':data["email"]}, 
                                            {"$set": 
                                                    {"historyOrders":history} #set the history orders with the total list
                                            }
                                        )

                    users.update_one( {'email':data["email"]},
                                            {"$set":
                                                    {"basket":[{'total_price':0}]} #reset user's basket
                                            }
                                        )

                    #print the receipt
                    return Response("Successful purchase!\nReceipt:\n" + json.dumps(cart, indent=4))
                else: #print error message
                    if len(data['card_number'])!=16:
                        return Response("Invalid card number.")
            else: #if user is an admin
                return Response("Admin cannot buy products - Login as a user.\n")
        else:
            return Response("There isn't a user with that email.")
    else: #user not authenticated
        return Response("User has not been authenticated.", status=401, mimetype='application/json')

@app.route('/printHistoryOrders', methods=['GET'])
def print_history_orders():
    #request JSON data message
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("Bad json content.", status=500, mimetype='application/json')
    if data == None:
        return Response("Bad request.", status=500, mimetype='application/json')
    if not "email" in data:
        return Response("Information incomplete.", status=500, mimetype="application/json")

    uuid = request.headers.get('Authorization') #get uuid from user
    if is_session_valid(uuid) : #if uuid is valid, then execute the entrypoint
        user = users.find_one({"email":data['email']})
        if user != None: #if user exists
            if user['category'] == 'user': #if user is not an admin then print their history orders
                return Response("Your order history: \n" + json.dumps(user["historyOrders"], indent=4))
            else: #if user is an admin
                return Response("Admin does not have history order.\n")
        else:
            return Response("There isn't a user with that email.")
    else: #user not authenticated
        return Response("User has not been authenticated.", status=401, mimetype='application/json')

#delete users
@app.route('/deleteUser', methods=['DELETE'])
def delete_user():
    # Request JSON data
    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("Bad json content.", status=500, mimetype='application/json')
    if data == None:
        return Response("Bad request.", status=500, mimetype='application/json')
    if not "email" in data:
        return Response("Information incomplete.", status=500, mimetype="application/json")

    uuid = request.headers.get('Authorization') #get uuid from user
    if is_session_valid(uuid) : #if uuid is valid, then execute the entrypoint
        user = users.find_one({"email":data["email"]}) #find user by email
        if user != None: #if user exists
            if user['category'] == 'user': #if user is not an admin
                users.delete_one(user) #delete
                user_name = user["name"] #insert in var the name of the user in order to print it later
                msg = user_name + " was deleted." #delete verification message
                return Response(msg, status=200, mimetype='application/json') #successful message and status
            else: #if user is an admin
                return Response("Admin cannot delete users - Login as a user.\n")
        else: #if user doesn't exist, print corresponding message
            return Response("There is no user with that email.")
    else: #user not authenticated
        return Response("User has not been authenticated.", status=401, mimetype='application/json')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
