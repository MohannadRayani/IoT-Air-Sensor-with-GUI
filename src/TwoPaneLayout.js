import React, { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  Title,
  TimeScale,
  Tooltip,
  Legend,
} from "chart.js";
import "chartjs-adapter-date-fns"; // For time formatting in the x-axis
import "./App.css";

// Register necessary Chart.js components
ChartJS.register(LineElement, PointElement, LinearScale, TimeScale, Title, Tooltip, Legend);

const AirSensorsRoom1 = () => {
  const [sensorData, setSensorData] = useState({
    pmsData: [],
    mq7Data: [],
    sgp40Data: [],
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Parallel fetching
        const [pmsResponse, mq7Response, sgp40Response] = await Promise.all([
          fetch("http://localhost:5000/pms/data/json"),
          fetch("http://localhost:5000/mq7/data/json"),
          fetch("http://localhost:5000/sgp40/data/json"),
        ]);

        // Parse responses
        const [pmsJson, mq7Json, sgp40Json] = await Promise.all([
          pmsResponse.json(),
          mq7Response.json(),
          sgp40Response.json(),
        ]);

        // Update state in one go to minimize re-renders
        setSensorData({
          pmsData: pmsJson,
          mq7Data: mq7Json,
          sgp40Data: sgp40Json,
        });
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    fetchData();
  }, []);

  const { pmsData, sgp40Data } = sensorData;

  // Prepare data for the chart
  const chartData = {
    labels: pmsData.map((entry) => entry.Timestamp), // Use timestamps for x-axis
    datasets: [
      {
        label: "PM1.0 (µg/m³)",
        data: pmsData.map((entry) => entry["PM1.0 (µg/m³)"]),
        borderColor: "blue",
        backgroundColor: "rgba(0, 0, 255, 0.2)",
        fill: true,
      },
      {
        label: "PM2.5 (µg/m³)",
        data: pmsData.map((entry) => entry["PM2.5 (µg/m³)"]),
        borderColor: "green",
        backgroundColor: "rgba(0, 255, 0, 0.2)",
        fill: true,
      },
      {
        label: "PM10 (µg/m³)",
        data: pmsData.map((entry) => entry["PM10 (µg/m³)"]),
        borderColor: "red",
        backgroundColor: "rgba(255, 0, 0, 0.2)",
        fill: true,
      },
      {
        label: "VOC Index",
        data: sgp40Data.map((entry) => entry.VOCI),
        borderColor: "purple",
        backgroundColor: "rgba(128, 0, 128, 0.2)",
        fill: true,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        type: "time", // Use time scale for x-axis
        time: {
          unit: "minute", // Group data points by minute
        },
        title: {
          display: true,
          text: "Time",
        },
      },
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: "Measurements",
        },
      },
    },
    plugins: {
      legend: {
        display: true,
        position: "top",
      },
      tooltip: {
        mode: "index",
        intersect: false,
      },
    },
  };

  return (
    <div className="container">
      <h1 className="title">Air Sensors in Room 1: CO, VOC, and PM1.0, 2.5, and 10</h1>
      <div style={{ height: "500px", width: "100%" }}>
        <Line data={chartData} options={chartOptions} />
      </div>
    </div>
  );
};

export default AirSensorsRoom1;
