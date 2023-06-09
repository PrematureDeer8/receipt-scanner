window.onscroll = function(){sticky()};

let identifier = 0;
let navbar = document.querySelector(".navigation");
let stick = navbar.offsetTop;
let error_bar = document.querySelector(".bar-container.error")
let yes = document.querySelector("#yes");
let no = document.querySelector("#no");
yes.onclick = () => {
    document.querySelector("#updateModal").style.display = "none";
    eel.download_update();
}
no.onclick = () => {
    document.querySelector("#updateModal").style.display = "none";
}

function sticky(){
    if(window.pageYOffset >= stick){
        navbar.classList.add("sticky");
    }else{
        navbar.classList.remove("sticky")
    }
}
document.querySelector("#uploadfiles").onchange = () => {
    let files = document.querySelector("#uploadfiles").files;
     if(files.length != 0){
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
        for(var i =0; i < files.length; i++){
            let name = files[i].name;
            let image_button = document.createElement("a");
            image_button.className = "image-tabs active";
            image_button.innerText = "Img"+(i+1);
            let grouper = document.createElement("div");
            grouper.id = files[i].name;
            grouper.className = "grouper";
            let polaroid = document.createElement("div");
            polaroid.className = "polaroid";
            let image = document.createElement("img");
            if(i != 0){
                grouper.style.display = "none";
                image_button.className = "image-tabs"
            }
            image.className = "image-content";
            image.src = "file:///"+ String(files[i].path);
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
                let active_grouper = document.getElementById(name);
                active_grouper.style.display = "block";
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
}
eel.expose(display_parsed_images)
function display_parsed_images(correspondence){
    const og_imgs  = Object.keys(correspondence);
    let validity = true;
    for(let og_img of og_imgs){
        let divider = document.getElementById(og_img);
        for(let parsed_image of correspondence[og_img]){
            let name = Object.keys(parsed_image)[0];
            let polaroid = document.createElement("div");
            polaroid.className = "polaroid";
            let container = document.createElement("div");
            container.className = "container";
            container.id = name;
            let overlay = document.createElement("div");
            overlay.className = "overlay";
            container.onclick = function(){
                if(overlay.style.height == "40%"){
                    overlay.style.height = "0";
                }else{
                    overlay.style.height = "40%";
                }
            }
            let p = document.createElement("p");
            p.innerText = name;
            let image = document.createElement("img");
            // caches.delete(
            //     "/images/parsed_receipts/"+name+".jpg"
            // );
            image.src = `file:///C:/ProgramData/Receipt-Scanner/images/parsed_receipts/${name}.jpg?=${identifier}`;
            identifier += 1;
            image.className = "parsed";
            for(let element in parsed_image[name]){
                let label = document.createElement("label");
                label.innerText = element;
                let input = document.createElement("input");
                if(element.toLowerCase() == "time" || element.toLowerCase() == "date"){
                    // <input type="Date or Time">
                    input.id = "date"
                    input.type = element.toLowerCase();
                    if(input.type == "time"){
                        input.id = "time"
                        input.step = "1";
                    }
                    if(parsed_image[name][element]["value"] != ""){
                        input.value = parsed_image[name][element]["value"];
                    }
                    input.required = true;
                    //check the validity of each input field with date or time type
                    // they all msut be valid
                    if(input.checkValidity() && validity){
                        validity = true;
                    }else{
                        validity = false;
                    }
                    input.onchange = function(){
                        // if input is valid then we must change
                        // the bottom border bar
                        // red danger bar takes precedence
                        if(input.checkValidity()){
                            container.classList.remove('danger-bar');
                            //check if there another empty field
                            let parent = input.parentElement;
                            for(let child of parent.children){
                                //get <input type="number">
                                if(child.type == "number" && child.value === ""){ 
                                    container.classList.add("warning-bar");
                                    break;
                                }   
                            }
                        }else{
                            if(container.classList.contains("warning-bar")){
                                container.classList.remove("warning-bar");
                            }
                            container.classList.add("danger-bar")
                        }
                        let dates = document.querySelectorAll("input[type='date']");
                        let times = document.querySelectorAll("input[type='time']");
                        let total_lengths = dates.length + times.length;
                        let true_counter = 0;
                        for(let date of dates){
                            if(date.checkValidity()){
                                true_counter += 1;
                            }
                        }
                        for(let time of times){
                            if(time.checkValidity()){
                                true_counter += 1;
                            }
                        }
                        if(total_lengths == true_counter){
                            document.querySelector(".submit-ocr").disabled = false;
                        }else{
                            document.querySelector(".submit-ocr").disabled = true;
                        }
                    }

                }else if(element.toLowerCase() ==  'type'){
                    input.type = "text";
                    input.id = "type";
                    if(parsed_image[name][element] != ""){
                        input.value = parsed_image[name][element]
                    }
                    input.placeholder = "Purchase Type";
                    input.onchange = function(){
                        if(input.value === ""){
                            container.classList.add("warning-bar");
                        }else{
                            container.classList.remove("warning-bar")
                        }
                    }
                }else{
                    if(element.toLowerCase() == "card"){
                        input.id = "card";
                    }else{
                        input.id = "total";
                    }
                    // <input type="number">
                    input.type = "number";
                    if(parsed_image[name][element]["value"] == ""){
                        input.placeholder = " ";
                    }else{
                        input.value = parsed_image[name][element]["value"]
                    }
                    input.placeholder = " ";
                    input.onchange = function(){
                        if(input.value == ""){
                            container.classList.add("warning-bar");
                        }else{
                            container.classList.remove("warning-bar")
                        }
                    }
                }
                overlay.append(label);
                overlay.append(document.createElement("br"));
                overlay.append(input);
                overlay.append(document.createElement("br"));
                if(element.toLowerCase() != "type"){
                    let highlight = document.createElement("div");
                    highlight.className = "highlight";
                    let left = parsed_image[name][element]["Left"]*100;
                    let height =parsed_image[name][element]["Height"]*100;
                    highlight.style.left = String(left)+"%";
                    highlight.style.height = String(height)+"%";
                    let width = parsed_image[name][element]["Width"]*100;
                    let top = parsed_image[name][element]["Top"]*700;
                    highlight.style.top = String(top)+"px";
                    highlight.style.width = String(width)+"%";
                    polaroid.append(highlight);
                }
            }

            container.append(p);
            polaroid.append(image);
            polaroid.append(overlay);
            polaroid.append(container);
            divider.append(polaroid);
        }
    }
    // all receipts are valid (1st time)
    if(validity){
        enable_convert();
    }
}
document.querySelector(".submit").onclick = () => {
    for(let bar of document.querySelectorAll(".bar-container")){
        bar.style.display = "none";
    }
    document.querySelector(".submit").disabled = true;
    let images = document.querySelectorAll(".image-content");
    let paths = [];
    for(let image of images){
        paths.push(String(image.src).substring(8));
    }
    eel.parse(paths);
}
eel.expose(enable_convert)
function enable_convert(){
    document.querySelector(".submit-ocr").disabled = false;
}
//onlick of convert button
function convert(){
    document.querySelector(".submit-ocr").disabled = true;
    let overlays = document.querySelectorAll(".overlay");
    let containers = document.querySelectorAll(".container");
    //one big dictionary for python
    let data  = {
        "filename": [],
        "date": [],
        "time": [],
        "type":[],
        "card":[],
        "total":[]
    }
    // arrays should match with index
    for(let container of containers){
        if(!(container.id === "")){
            data["filename"].push(`web/images/parsed_receipts/${container.id}.jpg`);
        }
    }
    for(let overlay of overlays){
        for(let child of overlay.children){
            console.log(child);
            if(child.tagName == "INPUT"){
                data[child.id].push(child.value);
            }
        }
    }
    eel.ocr(data);
}
eel.expose(disable_convert)
function disable_convert(){
    document.querySelector(".submit-ocr").disabled = True;
}
eel.expose(error_message)
function error_message(errors){ 
    let p = document.getElementById("message");
    // bar container
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
        let receipt_error = {}
        // console.log(errors);
        for(let key in errors){
            if(errors[key].length > 0){
                for(let id of errors[key]){
                    let container = document.getElementById(String(id));
                    // receipt_error hasn't initialized
                    if(receipt_error[String(id)] === undefined){
                        receipt_error[String(id)] = [];
                        receipt_error[String(id)].push(key);
                    }else{
                        receipt_error[String(id)].push(key)
                    }
                    if(container != undefined){
                        if(key == "Date"){
                            container.classList.add("danger-bar");
                        }else if(key == "Time"){
                            container.classList.add("danger-bar");
                        }
                        else if(!container.classList.contains("danger-bar")){
                            container.classList.add("warning-bar")
                        }
                    }
                }
            }
            counter += 1;
        }
        // Put errors into a readable string
        for(let receipt in receipt_error){
            if(receipt_error[receipt].length != 0){
                text += receipt + " has no: ";
                for(let error of receipt_error[receipt]){
                    if(receipt_error[receipt].indexOf(error) == (receipt_error[receipt].length-1)){
                        text += error + " "
                    }else{
                        text+= error +", "
                    }
                    
                }
                text += "\n"
            }
        }
        p.innerText = text;
        cls = " danger-bar"
    }
    
    parent.className += cls;
    parent.style.display = "block";
    parent.style.width = "93.8%";
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
        dialogbox.style.opacity = 0
        dialogbox.classList.remove("slide-right-small");
        void dialogbox.offsetWidth; // trigger reflow
        dialogbox.classList.add('slide-right-small-reverse'); // start animation  
        bool = false;
    }else{
        // document.querySelector(".import-export").style.backgroundColor = "rgb(238, 237, 237);"
        dialogbox.style.width = "15%";
        dialogbox.style.opacity = 1
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
document.querySelector(".close-error").onclick = () => {
    document.querySelector(".close-error").parentElement.style.display = 'none';
}
// modal for update
eel.expose(update_prompt)
function update_prompt(){
    let modal = document.querySelector("#updateModal");
    modal.style.display = "block"
}
eel.expose(convert_successful)
function convert_successful(){
    let success = document.querySelector("#success")
    success.innerText = "Convert completed!";
    success.parentElement.style = "display: block; width: 93.8%; top: 110px;" ;
}
function close_success(){
    document.querySelector("#success").parentElement.style.display = "none"
}