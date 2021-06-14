<h1>Ergasia_2_E18025_Vitsa_Panagiota</h1>

<h2>Introduction</h2>
<p>This project is made possible using mongodb database, python and flask. The execution of this application took place in linux, kali. It is written in python 3, implementing various entrypoints, such as get, post, update and delete.</p><br/>
<p>In this project the goal is to manage a market - a mongodb database named 'DSMarkets', including two types of users, admins and simple users each have a different category either 'admin' or 'user'. They have different possibilities, such as that only an admin can create the products of the collection, edit them or delete them.</p>
<p>Simple users can login, search for products based on their name, category or id, add products to their basket, see the content of their basket, delete products from the basket or checkout. They can also view their order history, or delete their account.</p>
<p>Those are all executed with a variety of different entrypoints.</p><br/>

<h2>Basic Functions</h2>
<p>First of, we've created some basic functions. Those are to help us create the user session, check validity of a specific session, get the content of both collections (Users, Products) and then two extra functions to create admins or simple users. We only have one admin and one user - though we can add more if we want.</p>

<img src="images/users.jpg"/><br/>

<h2>Admin Functions</h2>
<h3>Insert Product</h3>
<p>The admin is able to add products in the 'Products' collection of the 'DSMarkets' database.</p>

````python 
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
````

<p>Firstly, the admin gives their email in order to validate if they exist and are an admin.</p>
<p>If the id of the product doesn't exist in the collection 'Products', then the product doesn't already exist and procceeds to add it. Description is an optional field, so if the admin didn't enter it then it doesn't pass in the base.</p><br/>

<p>Command: </p>

````bash
curl -X UPDATE localhost:5000/insertProduct -d '{"email":"admin@email.com", "id":"005", "name":"peaches", "category":"fruits", "stock":"60", "price":"0.30"}' -H Content-Type:application/json
````

<p>Results: </p>
<img src="images/admin1.jpg"/>

<h3>Update Product</h3>
<p>The admin is able to update a product.</p>

````python 
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
````

<p>Firstly, the admin gives their email in order to validate if they exist and are an admin.</p>
<p>If the id of the product exists in the collection 'Products', then the product exists and then the program updates any of the fields given.</p><br/>

<p>Command: </p>

````bash
curl -X UPDATE localhost:5000/updateProduct -d '{"email":"admin@email.com", "id":"005", "price":"0.15", "stock":"80", "description":"fresh peaches"}' -H Content-Type:application/json
````

<p>Results: </p>
<img src="images/admin2.jpg"/>

<h3>Delete Product</h3>
<p>The admin is able to delete a product.</p>

````python 
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
````

<p>Firstly, the admin gives their email in order to validate if they exist and are an admin.</p>
<p>If the id of the product exists in the collection 'Products', then the product exists and the program deletes it.</p><br/>

<p>Command: </p>

````bash
curl -X DELETE localhost:5000/deleteProduct -d '{"email":"admin@email.com", "id":"005"}' -H Content-Type:application/json
````

<p>Results: </p>
<img src="images/admin3.jpg"/><br/>

<h2>Simple-User Functions</h2>
<h3>Login</h3>
<p>The simple user is able to login with their name password and email. The email is needed in order to identify them in the 'Users' collection.</p>

````python 
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
````

