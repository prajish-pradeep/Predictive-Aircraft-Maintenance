const joi = require("joi") //importing the "joi" library to validate the data as per schema

//validating the registration data
const registerValidation = (data)=> {
    const schemaValidation = joi.object({ //defining the schema and validation rules for register
        username:joi.string().required().min(3).max(256),
        email:joi.string().required().min(6).max(256).email(),
        password:joi.string().required().min(6).max(1024)
    })
    return schemaValidation.validate(data) //validation result
}

//validating the login data
const loginValidation = (data)=> {   //defining the schema and validation rules for login
    const schemaValidation = joi.object({
        email:joi.string().required().min(6).max(256).email(),
        password:joi.string().required().min(6).max(1024)
    })
    return schemaValidation.validate(data) //validation result
}

//exporting the validation functions
module.exports.registerValidation = registerValidation
module.exports.loginValidation = loginValidation

//references: 
//(Sotiriadis, 2022a-e)
//(Pradeepkumar, 2022)