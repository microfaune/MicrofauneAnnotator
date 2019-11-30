setTimeout(() => {

const filename = document
    .querySelector(".filename")
    .innerHTML.split("/")[2]
    .split(".")[0];
console.log('============', filename)
var blob = null;
var xhr = new XMLHttpRequest();
xhr.open("GET", `/media/${filename}.wav`);
xhr.responseType = "blob";
xhr.onload = function() {
    console.log("onload");
    blob = xhr.response;
    blob.name = `${filename}.wav`;
    blob.webkitRelativePath = `${filename}.wav`;
    sendDataToModel(blob);
};
xhr.send();




const sendDataToModel = (file) => {

    const formData = new FormData();
    formData.append("file", file);
    formData.name = file.filename;
    console.log(formData);

    const url = "http://127.0.0.1:5000";

    // const xhr = new XMLHttpRequest();
    // xhr.open("POST", url);
    // xhr.send(formData);

    // xhr.onreadystatechange = function() {
    //     console.log('===jjjkj')
    //     if (xhr.readyState == XMLHttpRequest.DONE) {
    //         plotData(xhr.responseText);
    //     }
    // }


    $.ajax({
        url : url,
        headers: {
            "content-type": "audio/wav"
        },
        type : "POST",
        data : file,
        success : function(json) {
            console.log("success");
            plotData(response);
        },
        error : function(xhr, errmsg, err) {
            console.log("Something went wrong: ", errmsg);
        }
    });
}



const plotData = (predictions) => {
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
        width: window.innerWidth,
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

}, 2000);
