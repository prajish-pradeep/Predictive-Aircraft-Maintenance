//Authentication

//importing the libraries
const express = require("express")
const router = express.Router()

const User = require("../models/User") //linking "User" with "auth.js"
const {registerValidation,loginValidation} = require("../validations/validation") //importing both the register and login validation

const bcryptjs = require("bcryptjs")  //encrypt and decrypt the password
const jsonwebtoken = require("jsonwebtoken") //generating auth-tokens

//register validations
router.post("/register", async(req,res)=>{
     //validation 1 to check user input (requirements)
     const {error} = registerValidation(req.body) //jump directly to the error
     
     if (error) {
          return res.redirect(`/register.html?error=${encodeURIComponent(error.details[0].message)}`) //if there is an error in validation, redirect to register page with error message
      }

     //validation 2 to check user already exist (using joi packets)
     const userExists = await User.findOne({email:req.body.email})
     if(userExists){
          return res.redirect("/register.html?error=User%20already%20exists") //if user email has been already registered, redirect to register page with error message "User already exists"
     }
     
     //creating a hashed representation of my password
     const salt = await bcryptjs.genSalt(5) //adding randomness and generating complexity
     const hashedPassword = await bcryptjs.hash(req.body.password,salt) //taking the passowrd and returning back with hashed representation
     
//code to insert data(new user document)
const user = new User({
     username:req.body.username,
     email:req.body.email,
     password:hashedPassword
 })
 try{
     await user.save() //saving user data in database
     res.redirect("/login.html") //redirecting to login page after successful registeration
 }catch(err){
     res.send({message:err}) //if there is an error, sending it back the error message
 }
})

//login validation
router.post("/login", async(req,res)=>{
     
     //validation 1 to check user input(meeting requirements)
     const {error} = loginValidation(req.body)
     if(error){
          return res.redirect(`/login.html?error=${encodeURIComponent(error.details[0].message)}`) //if there is an error in validation, redirect to login page with error message
     }   

     //validation 2 to check user exist (using joi)
     const user = await User.findOne({email:req.body.email})
     if(!user){
          return res.redirect("/login.html?error=User%20does%20not%20exist") //if user does not exist in database, redirect to login pafe with an error "User does not exist"
     }

     //validation 3 to check user password
     const passwordValidation = await bcryptjs.compare(req.body.password,user.password) 
     if(!passwordValidation){
          return res.redirect("/login.html?error=Password%20is%20incorrect") //if password is wrong, redirect to login page with an error "Password is incorrect"
     }
     
     //generating an auth-token
     const token = jsonwebtoken.sign({_id:user._id}, process.env.TOKEN_SECRET) //creating a json webtoken, and take the token secret and generate a token
     res.cookie("auth-token", token).redirect("/predict") //setting the auth-token as cookie, and then redirect to predict page
})

module.exports = router //exporting the authentication router

//references:
//(Sotiriadis, 2022a-e)
//(Pradeepkumar, 2022)