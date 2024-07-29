const mongoose = require("mongoose") //importing the mongoose library

const userSchema = mongoose.Schema({ //users should have username, email and password mandatorily as defined
    username:{
        type:String,
        require:true,
        min:3,
        max:256
    },
    email:{
        type:String,
        require:true,
        min:6,
        max:256
    },
    password:{
        type:String,
        require:true,
        min:6,
        max:1024 //password characters needed to be long since password needs to be hashed
    },
    date:{ //keeping track of date when user was signed up
        type:Date,
        default:Date.now
    },
}) 

module.exports= mongoose.model("users",userSchema) //mapping as per the mongodb database name

//references: 
//(Sotiriadis, 2022a-e)
//(Pradeepkumar, 2022)