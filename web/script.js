eel.expose(display_images)
function display_images(file_names){
    document.querySelector(".progress").style = "width: 0%";
    document.querySelector(".submit").disabled = false;
    let prev_buttons = document.querySelectorAll(".image-tabs");
    let prev_images = document.getElementsByTagName("img");
    let grouper = document.querySelectorAll(".grouper");
    for(let button of prev_buttons){
        button.remove();
    }
    for(let image of prev_images){
        image.remove();
    }
    for(let group of grouper){
        group.remove();
    }
    document.querySelector(".tab-content").style.display = "block";
    let image_display = document.querySelector(".image-tab")
    let image_content = document.querySelector(".tab-content")
    for(let name of file_names){
        let image_button = document.createElement("button");
        image_button.className = "image-tabs active";
        image_button.innerText = "Image"+(file_names.indexOf(name)+1);
        let grouper = document.createElement("div");
        grouper.id = name;
        grouper.className = "grouper";
        let image = document.createElement("img");
        if(file_names.indexOf(name) != 0){
            grouper.style.display = "none";
            image_button.className = "image-tabs"
        }
        image.className = "image-content";
        image.src = "images/scanned_receipts/"+name;
        //*
        image_button.addEventListener("click", function (){
            let buttons = document.querySelectorAll(".image-tabs");
            for(let button of buttons){
                button.className = "image-tabs"
            }
            let dividers;
            dividers = document.querySelectorAll(".grouper");
            for(let divider of dividers){
                divider.style.display = "none";
            }
            document.getElementById(name).style.display = "block";
            image_button.className += " active";

        });
        grouper.append(image);
        image_display.append(image_button)
        image_content.append(grouper);
        
    }
}
eel.expose(display_parsed_images)
function display_parsed_images(correspondence){
    const og_imgs  = Object.keys(correspondence);
    for(let og_img of og_imgs){
        let divider = document.getElementById(og_img);
        for(let parsed_image of correspondence[og_img]){
            let image = document.createElement("img");
            image.src = "images/parsed_receipts/"+parsed_image+".jpg";
            image.className = "parsed";
            divider.append(image);
        } 
    }
}
document.querySelector(".pick-file").onclick = () => {
    document.querySelector(".bar-container").style.display = "none";
    document.querySelector(".pick-file").disabled = true;
    eel.windowfilepicker();
};
document.querySelector(".submit").onclick = () => {
    document.querySelector(".bar-container").style.display = "none";
    document.querySelector(".submit").disabled = true;
    eel.parse();
    $("#ocr").load("ocr.html");
}
function submit_ocr() {
    // console.log(document.querySelector(".submit-ocr"))
    document.querySelector(".submit-ocr").disabled = true;
    eel.ocr();
}
eel.expose(reable_excel_button)
function reable_excel_button(){
    document.querySelector(".submit-ocr").disabled = false;
}
eel.expose(error_message)
function error_message(message){
    let p = document.getElementById("message");
    p.innerText = message;
    let parent = p.parentElement;
    parent.className += " danger-bar"
    parent.style.display = "block"
}
eel.expose(progress_bar)
function progress_bar(done){
    document.querySelector(".progress-bar").style = "display: block;";
    let total_images = document.querySelectorAll(".image-tabs").length;
    let width = (done)/total_images;
    let progress = document.querySelector(".progress");
    progress.innerText = Math.round((width)*100) + "%";
    progress.style = "width: " + progress.innerText;

}
eel.expose(reable_browse);
function reable_browse(){
    document.querySelector(".pick-file").disabled = false;
}