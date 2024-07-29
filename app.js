//importing the libraries
const express = require("express") 
const mongoose = require("mongoose") 
const bodyParser = require("body-parser") //parsing incoming request bodies
const dotenv = require("dotenv")
const path = require("path") //for working with file and directory

const auth = require("./verifyToken") //authentication and token verification
const cookieParser = require("cookie-parser") //parsing cookies from request headers

//initiaising the express app
const app = express()
app.set("view engine", "ejs")

//loading environment variables from .env file
dotenv.config({path: "./secret_keys/.env"})

//middleware to parse url encoded bodies
app.use(express.urlencoded({extended: true}))

//body parser middleware to parse incoming request bodies
app.use(bodyParser.json())

//setting static folder
app.use(express.static("public"))

//middleware to parse cookies
app.use(cookieParser())

//importing the route modules
const authRoute = require("./routes/auth")
const datasetRoutes = require("./routes/dataset")

//registring the route from route modules
app.use("/", authRoute) //user authentication
app.use("/", datasetRoutes) //dataset operation

//route for the home page
app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "public/index.html"))
})

//route for the register page
app.get("/register", (req, res) => {
    res.sendFile(path.join(__dirname, "public/register.html"))
})

//route for the login page
app.get("/login", (req, res) => {
    res.sendFile(path.join(__dirname, "public/login.html"))
})

//route for the predict page, and is protected by auth to make sure logged in user can only access
app.get("/predict", auth, (req, res) => {
    res.sendFile(path.join(__dirname, "public/predict.html"))
})

//handling user logout and clearing auth cookies
app.get("/logout", (req, res) => {
    res.clearCookie("auth-token")
    res.redirect("/") //redirect to homepage
})

//connecting to MongoDB
async function connectToDb() {
    try {
        await mongoose.connect(process.env.DB_CONNECTOR, { useNewUrlParser: true, useUnifiedTopology: true })
        console.log("MangoDB is connected")
    } catch (err) {
        console.error("Failed to connect to MongoDB:", err.message)
    }
}
connectToDb()

// //starting the server and listening on port 3000
// app.listen(3000, () => {
//     console.log("Server is up and running on port 3000 for Aircraft Maintenance System!")
// })

// defining the port for google app engine deployment
const PORT = process.env.PORT || 3000
app.listen(PORT, () => {
    console.log("Server is up and running for Aircraft Maintenance System!")
})

//references:
//(Victor, 2023)
//(Tabnine, 2023b)
//(Node.js Documentation, 2023)