//importing the libraries
const express = require("express")
const router = express.Router()
const { Storage } = require("@google-cloud/storage") //importing google cloud client library
const dotenv = require("dotenv")
dotenv.config({ path: "./secret_keys/.env"}) //for working with file and directory
const multer = require("multer") //handling multipart/form data(uploading files)
const upload = multer({ dest: "uploads/" }) //directory for uploading files
//const memorystorage = multer.memoryStorage()
//const upload = multer({ storage: memorystorage })
const path = require("path") 
const predict = path.join(__dirname, "predict.py") //path for python prediction script
const monitor = path.join(__dirname, "monitor.py")
const { exec } = require("child_process") //executing shell commands

//initialising and configuring google cloud storage
const storage = new Storage({
  projectId: process.env.PROJECT_ID, //getting project ID
})

const bucketName = process.env.BUCKET_NAME //getting bucket name
const bucket = storage.bucket(bucketName) //accessing the gcp bucket

//defining and handling prediction requests
router.post("/predict", upload.single("file"), async (req, res) => {
  try {

    //checking dataset is provided while submitting the request in predict page
      if (!req.file) {
          console.log("no files uploaded")
          return res.send("No Files Uploaded")
      }

      const dataset = req.file //extracting the dataset
      const destination = req.file.originalname //setting the original name for the dataset in gcp storage

      //uploading the dataset to GCP bucket
      await bucket.upload(dataset.path, { destination: destination }, (err) => {
          //checking if there is any error during the upload
          if (err) { 
              console.log("Error uploading file")
          } else {
              console.log("File uploaded in GCP")
          }
      })
      
      //defining and storing the path of uploaded file
      file_path = `${bucketName}/${destination}`
      process.env.file_path = file_path 

      //executing the python prediction script with the dataset from GCP
      exec(`python3 "${predict}" "file_path"`, (error, stdout) => {
          if (error) {
              console.error("Error during python execution", error.message) //logging error message to the console
              return res.send("Error occurred during prediction")
          }

          //parsing the prediction result and sending the response
          try {
              const predictions = JSON.parse(stdout)
              //formatting the prediction as we only need to show Unit_ID(engine number) and their respective RUL
              const RUL_predictions = predictions.map((prediction) => ({ 
                  Unit_ID: prediction.Unit_ID, //extracting Unit_ID from prediction results
                  RUL: prediction.RUL //extracting RUL
              }))

              console.log("Sending predictions")
              res.render("result", {data:RUL_predictions}) //sending the formatted predictions
              //console.log(RUL_predictions)
            }
            //catching the error when parsing json output
            catch (parseError) {
              console.error("Failed to parse JSON", stdout) //logging problem output to the console
              return res.send("Error parsing prediction results")
            }
      })
  }  
    //catching other general errors during the process
    catch (err) {
      console.error("Error processing the request:", err.message) //logging error message to the console
      res.send("Error occurred while processing the request")
    }
})

router.post("/predict/monitor", upload.single("file"), async (req, res) => {
  try {
    //checking dataset is provided while submitting along with the request
    if (!req.file) {
      console.log("no files uploaded")
      return res.send("No Files Uploaded")
    }

    const dataset = req.file //extracting the data
    const destination = req.file.originalname //setting the name as the file name of the dataset in gcp storage

    //uploading the dataset in GCP bucket
    await bucket.upload(dataset.path, {destination: destination}, (err) => {
      //checking if there is any error during the upload
      if (err) { 
        console.log("Error uploading file")
      } else {
        console.log("File uploaded in GCP")
      }
    })

    //defining and storing the path of uploaded file
    file_path = `${bucketName}/${destination}`
    process.env.file_path = file_path

    //executing monitor_and_alert_system
    exec(`python3 "${monitor}" "file_path1"`, (error, stdout, stderr) => {
      if (stderr) {
        console.error("Python error:", stderr)  //logging error message to the console
      }

      //returning the alerts from the monitoring
      res.send(stdout) //capturing standard output
      console.log("Alerts sent")
    })

  } catch (err) {
    console.error("Error processing the request:", err.message) //logging error message to the console
    res.send("An error occurred while processing the request")
  }
})

router.get("/predict/monitor", (req,res) =>{ //redirecting to predict path
  res.redirect("/predict")
})


module.exports = router //exporting the router

//references: 
//(Google APIs, 2023)
//(Google Storage Documentation, 2023a)
//(Google Cloud Documentation, 2023)
//(Tabnine, 2023a)
//(Hossain, 2023)
//(Yaapa, 2022)
//(W3 Schools, 2023)
//(Digital Ocean, 2020)
//(Node.js Documentation, 2023)

