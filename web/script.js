eel.expose(display_images)
function display_images(file_names){
    console.log(file_names)
    let center = document.querySelector(".center")
    for(let name of file_names){
        let image = document.createElement("img");
        image.src = "images/scanned_receipts/"+name;
        image.width = 300
        image.height = 300
        // image.style.margin = 50
        center.append(image);
    }
}
eel.expose(display_parsed_images)
function display_parsed_images(file_names){
    let line_break = document.createElement("br");
    let center = document.querySelector(".center");
    center.append(line_break);
    for(let name of file_names){
        let image = document.createElement('img');
        image.src = "images/parsed_receipts/"+name;
        image.width = 100
        image.height = 300
        center.append(image);
    }
    console.log(file_names)
}
document.querySelector(".pick-file").onclick = () => {
    eel.windowfilepicker();
};
document.querySelector(".submit").onclick = () => {
    eel.parse();
    $("#ocr").load("ocr.html");
}
function submit_ocr() {
    eel.ocr();
    console.log("Task has been completed excel file created")
}