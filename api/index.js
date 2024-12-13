const express = require("express");
const path = require("path");
const fs = require("fs");
const multer = require("multer");
const csvtojson = require("csvtojson");
const cors = require("cors");
const os = require("os");

const app = express();
const PORT = 5000;

// Folder for uploads
const UPLOAD_FOLDER = path.join(__dirname, "uploads"); 
const UPLOAD_FILE_PATHS = {
  pms: path.join(UPLOAD_FOLDER, "pmsdata.csv"), // File path for PMS data
  mq7: path.join(UPLOAD_FOLDER, "mq7data.csv"), // File path for MQ7 data
  sgp40: path.join(UPLOAD_FOLDER, "sgp40data.csv") // File path for SGP40 data
};

// Ensure the uploads folder exists
if (!fs.existsSync(UPLOAD_FOLDER)) {
  fs.mkdirSync(UPLOAD_FOLDER);
}

app.use((req, res, next) => {
  const timestamp = new Date().toISOString(); // Current timestamp
  const method = req.method; // HTTP method (GET, POST, etc.)
  const url = req.url; // Requested URL

  // Determine the IP address of the client
  const ip =
    req.headers["x-forwarded-for"] || // Check if the app is behind a proxy
    req.socket.remoteAddress || // Directly connected
    null;

  const logMessage = `[${timestamp}] ${method} request to ${url} from IP: ${ip}`;
  console.log(logMessage);

  // Save the log to a file
  fs.appendFileSync("access_logs.txt", logMessage + "\n");

  next(); // Pass control to the next middleware or route handler
});

// Set up Multer for handling file uploads
const upload = multer({
  dest: UPLOAD_FOLDER, // Save uploaded files in the uploads folder
});

// Middleware
app.use(express.json());

app.use(cors({
  origin: "http://localhost:3000",
  methods: "GET, POST, PUT, DELETE, OPTIONS",
  credentials: true,
  exposedHeaders: ["mq-7", "sgp40", "pms"], // Allow the custom header to be exposed

}));
// Helper function to handle upload and append logic
const handleFileUpload = (filePath) => (req, res) => {
  if (!req.file) {
    return res.status(400).send("No file uploaded.");
  }

  const tempFilePath = req.file.path;

  // Read the uploaded file
  fs.readFile(tempFilePath, "utf8", (err, data) => {
    if (err) {
      console.error("Error reading uploaded file:", err);
      return res.status(500).send("Failed to process the uploaded file.");
    }

    // Check if the target file exists
    const fileExists = fs.existsSync(filePath);

    // Split the file into lines and remove the headers if the target file already exists
    const lines = data.split("\n");
    const contentToAppend = fileExists ? lines.slice(1).join("\n") : data;

    // Append content to the constant file
    fs.appendFile(filePath, contentToAppend, (appendErr) => {
      // Delete the temp file after processing
      fs.unlinkSync(tempFilePath);

      if (appendErr) {
        console.error("Error appending to the CSV file:", appendErr);
        return res.status(500).send("Failed to append data to the file.");
      }

      console.log(`Appended data to ${filePath}`);
      res.status(200).send("File uploaded and appended successfully.");
    });
  });
};

// Helper function to get JSON from a CSV file
const handleJsonResponse = (filePath) => (req, res) => {
  if (!fs.existsSync(filePath)) {
    return res.status(404).send("CSV file not found.");
  }

  csvtojson()
    .fromFile(filePath)
    .then((json) => {
      res.json(json);
    })
    .catch((error) => {
      console.error("Error converting CSV to JSON:", error);
      res.status(500).send("Failed to convert CSV to JSON.");
    });
};

// PMS Data Endpoints
app.post("/pms/data", upload.single("file"), handleFileUpload(UPLOAD_FILE_PATHS.pms));
app.get("/pms/data/json", handleJsonResponse(UPLOAD_FILE_PATHS.pms));

// MQ7 Data Endpoints
app.post("/mq7/data", upload.single("file"), handleFileUpload(UPLOAD_FILE_PATHS.mq7));
app.get("/mq7/data/json", handleJsonResponse(UPLOAD_FILE_PATHS.mq7));

// SGP40 Data Endpoints
app.post("/sgp40/data", upload.single("file"), handleFileUpload(UPLOAD_FILE_PATHS.sgp40));
app.get("/sgp40/data/json", handleJsonResponse(UPLOAD_FILE_PATHS.sgp40));

// Start the server
app.listen(PORT, () => {
  // Get the local IP address of the machine
  const networkInterfaces = os.networkInterfaces();
  let localIp = "localhost";

  for (const interfaceName in networkInterfaces) {
    for (const net of networkInterfaces[interfaceName]) {
      if (net.family === "IPv4" && !net.internal) {
        localIp = net.address;
        break;
      }
    }
    if (localIp !== "localhost") break;
  }

  console.log(`Server is running on http://${localIp}:${PORT}`);
});
