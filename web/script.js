eel.expose(display_images)
function display_images(file_names){
    prev_buttons = document.querySelectorAll(".image-tabs");
    prev_images = document.getElementsByTagName("img");
    if(prev_buttons.length > 0 ){
            //everything shifts up one when you delete
            for(var i = 0; i < prev_buttons.length; i++){
                prev_buttons[i].remove();
                prev_images[0].remove();
                // console.log(prev_buttons[i]);
        }
    }
    document.querySelector(".tab-content").style.display = "block";
    let image_display = document.querySelector(".image-tab")
    let image_content = document.querySelector(".tab-content")
    for(let name of file_names){
        let image_button = document.createElement("button");
        image_button.className = "image-tabs";
        image_button.innerText = "Image"+(file_names.indexOf(name)+1);
        let image = document.createElement("img");
        if(file_names.indexOf(name) != 0){
            image.style.display = "none";
        }
        image.id = name;
        image.className = "image-content";
        image.src = "images/scanned_receipts/"+name;
        //*
        image_button.addEventListener("click", function (){
            let tab_images;
            tab_images = document.getElementsByTagName("img");
            for(let image of tab_images){
                image.style.display = "none";
            }
            document.getElementById(name).style.display = "block";

        });
        
        image_display.append(image_button)
        image_content.append(image);
        
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
    // console.log(file_names)
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