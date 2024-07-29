const jsonwebtoken = require('jsonwebtoken') //importing the library for handling json webtokens

//creating a function to authenticate users based on tokens
function auth(req,res,next){    
    const token = req.header('auth-token') || (req.cookies && req.cookies['auth-token']) //retrieving token from headers or cookies
    if(!token){     //if token is not present in header or cookies, access should not be granted
        return res.status(401).send({message:'Access denied'})
    }
    try{
        const verified = jsonwebtoken.verify(token,process.env.TOKEN_SECRET) //verify the token with secret key
        req.user=verified
        next() //continue to next middleware
    }catch(err){  //if token is wrong, access should not be granted
        return res.status(401).send({message:'Invalid token'})
    }
}

module.exports=auth //exporting the auth middleware

//references: 
//(Sotiriadis, 2022a-e)
//(Pradeepkumar, 2022)