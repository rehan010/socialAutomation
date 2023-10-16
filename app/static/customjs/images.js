
function decorateMedia(){
    const mediadivs = document.querySelectorAll('.media-div');


    if (mediadivs.length > 0){
        mediadivs.forEach( div => {
            const anchors = div.querySelectorAll('.photos');
            var i =0;
            if (anchors.length>0){
                for(var j=0; j<anchors.length;j++){
                    if(i!=0){
                        anchors[i].classList.add('-ml-4');
                    }
                    i++;
                }
            }
        })

}





}

