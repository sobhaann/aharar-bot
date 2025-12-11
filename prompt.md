# How are you?

your a senior backend dev that your speciallity in createing telegram bots using python. you love to use type hinting in your program.

# What is your task:

you and your friend found a charity and your friend wants to create a telegram bot to notify users to pay their donations.
the estimated number of users is 100 and for this reason i decided to use sqlite because it is lightweight

# task details:
    1. we have two database table, one called users and other called payments. the users table is a seeded table that its data located in "./data/seed_data.csv" this csv contains the data of user table

    2. because our user is iranin we should consider to set the timezone to: Asia/Tehran and our calander mus be jalali clander

    3. the message templates are located in "./messages.md" 

    4. when a user first start the bot it should enter his respective pin code that is in the "./data/seed_data.csv" and if the pin code is incorecct we dont let him to use the bot until admin aprove it.

    5. at 3th of each month we should notify the users to pay their donations (consider that i mean the 3th of jalali calander)

    6. if the payment status of a user is failed or pending we should send another notify message to the user and remind him to pay their donations in the 7th of month(consider that i mean the 7th of jalali calander)

    7. in the 10th of the month we should give admin an excel file and a pdf file of the summary of this month.

    8. when user upload the payment image to the bot. the bot should send the image to the admin and amdin can approve or deny the image. if the image denied we should send a message to the user that his payment is denied and you should contact the admin. and if his payment is approved we should send a message to the user and appriciate his payment.

# considirations:
    1. please use pydantaic to sanitize the datatypes
    2. please create a dockerfile
    3. consider this use a sqlite viewer in the docker-compose.yml file to see the data.
    4. you allowed to only create readme.md file for explanation what you do. please dont create any .md file