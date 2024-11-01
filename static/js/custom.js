if (
  $("#default-table").length &&
  typeof simpleDatatables.DataTable !== "undefined"
) {
  const dataTable = new simpleDatatables.DataTable("#default-table", {
    searchable: true,
    sortable: true,
    perPage: 5,
  });
}

$(".show-details").on("click", function () {
  const bookId = $(this).data("book-id");
  const modalBody = $(`#modal-body-${bookId}`);

  $.ajax({
    url: `/dashboard/book/${bookId}/details`,
    method: "GET",
    success: function (response) {
      let html = "";

      if (response.description) {
        html += `
                    <div class="mb-4">
                        <h4 class="text-lg font-semibold mb-2 text-gray-900">Description</h4>
                        <p class="text-gray-600">${response.description}</p>
                    </div>
                `;
      }

      if (response.table_of_contents) {
        html += `
                    <div>
                        <h4 class="text-lg font-semibold mb-2 text-gray-900">Table of Contents</h4>
                        <p class="text-gray-600 mb-2">${response.table_of_contents}</p>
                    </div>
                `;
      }

      if (!response.description && !response.table_of_contents) {
        html =
          '<p class="text-gray-600">No detailed information available.</p>';
      }

      modalBody.html(html);
    },
    error: function (xhr, status, error) {
      modalBody.html(`
                <div class="text-red-500">
                    Failed to load book details. Please try again later.
                </div>
            `);
      console.error("Error:", error);
    },
  });
});

$(".btn-delete").on("click", function (e) {
  e.preventDefault();
  const form = $(this).closest(".delete-form");

  Swal.fire({
    title: "Are you sure?",
    text: "Do you really want to delete this book?",
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#d33",
    cancelButtonColor: "#3085d6",
    confirmButtonText: "Yes, delete it!",
  }).then((result) => {
    if (result.isConfirmed) {
      Swal.fire("Deleted!", "Your book has been deleted.", "success");
      form.submit();
    }
  });
});

$("#cover").on("change", function () {
  const fileName = this.files[0]?.name;
  $("#file-name").text(fileName || "No file selected");
});
