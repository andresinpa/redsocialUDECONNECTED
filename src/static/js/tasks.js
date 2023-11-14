const taskComplete = document.getElementById("complete"),
      taskIncomplete = document.getElementById("incomplete"),
      addBtn = document.querySelector(".btn-success"),
      quitBtn = document.querySelector(".btn-danger");


taskComplete.addEventListener("click", e => {
    addBtn.classList.add("hide");
    quitBtn.classList.remove("hide");
})
taskIncomplete.addEventListener("click", e => {
    quitBtn.classList.add("hide");
    addBtn.classList.remove("hide");
})