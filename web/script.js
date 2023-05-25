window.onscroll = function(){sticky()};

let navbar = document.querySelector(".navigation");
let stick = navbar.offsetTop;

function sticky(){
    if(window.pageYOffset >= stick){
        navbar.classList.add("sticky");
    }else{
        navbar.classList.remove("sticky")
    }
}
eel.expose(display_images)
function display_images(file_names){
    document.querySelector(".submit-ocr").disabled = true;
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
    let image_display = document.querySelector(".navigation")
    let image_content = document.querySelector(".tab-content")
    for(let name of file_names){
        let image_button = document.createElement("a");
        image_button.className = "image-tabs active";
        image_button.innerText = "Img"+(file_names.indexOf(name)+1);
        let grouper = document.createElement("div");
        grouper.id = name;
        grouper.className = "grouper";
        let polaroid = document.createElement("div");
        polaroid.className = "polaroid";
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
        let container = document.createElement("div");
        container.className = "container";
        let p = document.createElement("p");
        p.innerText = "Original Image";
        container.append(p);
        polaroid.append(image);
        polaroid.append(container);
        grouper.append(polaroid);
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
            let polaroid = document.createElement("div");
            polaroid.className = "polaroid";
            let container = document.createElement("div");
            container.className = "container";
            container.id = parsed_image;
            console.log(correspondence[og_img].indexOf(parsed_image))
            let p = document.createElement("p");
            p.innerText = parsed_image;
            let image = document.createElement("img");
            image.src = "images/parsed_receipts/"+parsed_image+".jpg";
            image.className = "parsed";
            container.append(p);
            polaroid.append(image);
            polaroid.append(container);
            divider.append(polaroid);
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
}
eel.expose(enable_convert)
function enable_convert(){
    document.querySelector(".submit-ocr").disabled = false;
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
function error_message(errors){ 
    let p = document.getElementById("message");
    let parent = p.parentElement;
    parent.classList.remove('danger-bar');
    parent.classList.remove('warning-bar');
    let cls;
    if(errors["Exists"]){
        p.innerText = errors["message"];
        cls = " danger-bar";
    }else if(errors["NO AWS"]){
        p.innerText = "Check internet connection to convert to excel!";
        cls = " danger-bar";
    }else if(errors["Open Excel"]){
        let file_name = errors["filename"];
        p.innerText = file_name + " is opened! Please close before proceeding.";
        cls = " danger-bar";
    }else if(errors["Duplicate"] != undefined && errors["Duplicate"].length > 0){
        let text = "Duplicates:\n";
        let counter = 0;
        for(let receipt of errors["Duplicate"]){
            let container = document.getElementById(String(receipt));
            container.className += " warning-bar";
            if(counter != (errors["Duplicate"].length-1)){
                text += receipt +", ";
            }else{
                text += receipt;
            }
            counter += 1;
        }
        p.innerText = text;
        cls = " warning-bar";
    }else{
        let counter = 0;
        let text = "";
        for(let key in errors){
            if(counter > 1){
                let container = document.getElementById(String(key));
                if(container != undefined && errors[key].length > 0){
                    text+= String(key) + ": "
                    container.className += " danger-bar";
                    for(let error of errors[key]){
                        text += error + " "
                    }        
                    text+= "\n";
                }
            }
            counter += 1;
        }
        p.innerText = text;
        cls = " danger-bar"
    }
    
    parent.className += cls
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
let bool = true;
document.querySelector(".import-export").onclick = () => {
    // document.querySelector(".import-export").style.background-color = rgb(193, 193, 193);
    let dialogbox = document.querySelector(".dialogbox");
    if(bool){
        // document.querySelector(".import-export").style.backgroundColor = "rgb(193, 193, 193);"
        dialogbox.style.width = "0%";
        dialogbox.style.opacity = "0%"
        dialogbox.classList.remove("slide-right-small");
        void dialogbox.offsetWidth; // trigger reflow
        dialogbox.classList.add('slide-right-small-reverse'); // start animation  
        bool = false;
    }else{
        // document.querySelector(".import-export").style.backgroundColor = "rgb(238, 237, 237);"
        dialogbox.style.width = "15%";
        dialogbox.style.opacity = "100%"
        dialogbox.classList.remove('slide-right-small-reverse'); // start animation
        void dialogbox.offsetWidth; // trigger reflow
        dialogbox.classList.add('slide-right-small'); // start animation  
        bool = true;
    }
}
function preferences(){
    let display = document.getElementById("prefModal").style.display;
    if(display == "" || display == "none"){
        document.getElementById("prefModal").style.display = "block";
    }
}
async function file_path(){
    if(document.querySelector(".input").value == ""){
        let value = await eel.default_file_path()();
        document.querySelector(".input").value = value;
    }
}
async function count_dup(){
    let value = await eel.default_count_dup()();
    document.querySelector(".duplicate").checked = value;
}
eel.expose(get_path);
function get_path(){
    // console.log(document.querySelector(".input").value)
    return document.querySelector(".input").value;
}
eel.expose(count_duplicates)
function count_duplicates(){
    return document.querySelector(".duplicate").checked
}
document.querySelector(".close").onclick = () => {
    document.getElementById('prefModal').style.display = 'none'
    eel.updateperferences(document.querySelector(".input").value,document.querySelector(".duplicate").checked)
}
