
// const filename = document
//     .querySelector(".filename")
//     .innerHTML.split("/")[2]
//     .split(".")[0];
// console.log('============', filename)
// var blob = null;
// var xhr = new XMLHttpRequest();
// xhr.open("GET", `/media/${filename}.wav`);
// xhr.responseType = "blob";
// xhr.onload = function() {
//     console.log("onload");
//     blob = xhr.response;
//     blob.name = `${filename}.wav`;
//     blob.webkitRelativePath = `${filename}.wav`;
//     sendDataToModel(blob);
// };
// xhr.send();

const sendDataToModel = (blob) => {
    const formData = new FormData();
    formData.append("file", blob, blob.name);

    const url = "http://127.0.0.1:5000";

    $.ajax({
        url : url,
        contentType: false,
        type : "POST",
        data : formData,
        processData: false,
        success : function(response) {
            console.log("success");
            plotData(JSON.parse(response));
        },
        error : function(xhr, errmsg, err) {
            console.log("Something went wrong: ", errmsg);
        }
    });
}

const plotData = (predictions) => {
    const width = document.querySelector(".audio_visual > wave > canvas").offsetWidth;
    document.querySelector(".audio_visual").style.width = `${width}px`;
    document.querySelector("#plot-container").style.width = `${width}px`;
    document.querySelector(".labels").style.width = `${width}px`;
    const data = [
        {
            y: predictions,
            type: "scatter",
            mode: "lines",
            marker: { color: "#2EBCE7" },
            rangemode: "nonnegative"
        }
    ];
    const layout = {
        xaxis: {
            range: [0, predictions.length],
            showgrid: false
        },
        yaxis: {
            range: [0, 1],
            showgrid: false
        },
        width: width,
        dragmode: "pan",
        height: 200,
        autosize: false,
        margin: {
            l: 0,
            r: 0,
            b: 0,
            t: 0,
            pad: 0
        }
    };

    Plotly.newPlot("plot-container", data, layout);
}
