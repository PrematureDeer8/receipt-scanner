
eel.expose(read_path)
function read_path(type){
    let input = document.getElementById("folder-input");
    let path = input.value;
    if(path == ""){
        console.log("Undefined");
    }else{
        console.log(path);
    }
}

let fileHandles;
let allContent;
const options = {
 multiple: true,
};
 
document.querySelector(".pick-file").onclick = async () => {
 fileHandles = await window.showOpenFilePicker(options);
 
 allContent = await Promise.all(
   fileHandles.map(async (fileHandle) => {
     const file = await fileHandle.getFile();
    //  const content = await file.arrayBuffer();
     return file;
   })
 );
 
 let paragraphs = document.querySelectorAll(".image-name");
 if(paragraphs.length > 0){
    for(let paragraph of paragraphs){
        paragraph.remove();
    }
 }

 for(let image of allContent){
    let p = document.createElement("p");
    p.className = "image-name"
    p.innerText = image.name;
    document.querySelector(".center").append(p)
 }
};
document.querySelector(".submit").onclick = async () =>{
    if(allContent == undefined){
        alert("No images selected");
    }else{
        let data = [];
        for(let file of allContent){
            let reader = new FileReader();
            let blob = new Blob([await file.text()],{type: "text"});
            reader.readAsDataURL(blob);
            reader.onloadend = function () {
                var string = reader.result;
                if(allContent.length > 1){
                   data.push(string); 
                }else{
                    data = string
                    eel.pass_images(data);
                }
                
            }
            
        }
        console.log(data)
       if(data.length != 0 ){
            console.log(data)
            eel.pass_images(data);
       }
        
    }
    
}