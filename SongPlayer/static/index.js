audios = document.getElementsByClassName("songplayer")

for (var i = 0; i < audios.length; i++) {
    const playnext = ()=>{
        try{
        audios[i+1].play()
        console.log("played")
        }
        catch(e){
            console.log(e)
        }
        finally{
            while (false){}
        }
    }
    audios[i].addEventListener('ended', playnext, false);
}

function set(){
    song_name = document.getElementById("name").textContent
    window.location.replace('/playlists/add/' + song_name)
}
