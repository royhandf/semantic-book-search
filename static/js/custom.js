// $("#description").summernote({
//   placeholder: "Write a description here",
//   tabsize: 2,
//   height: 200,
//   toolbar: [
//     ["style", ["bold", "italic", "underline", "clear"]],
//     ["font", ["strikethrough", "superscript", "subscript"]],
//     ["para", ["ul", "ol", "paragraph"]],
//     ["insert", ["link"]],
//     ["view", ["fullscreen", "codeview", "help"]],
//   ],
//   popover: {
//     image: [],
//     link: [],
//     air: [],
//   },
// });

// $("#table_of_contents").summernote({
//   placeholder: "Write a description here",
//   tabsize: 2,
//   height: 200,
//   toolbar: [
//     ["style", ["bold", "italic", "underline", "clear"]],
//     ["font", ["strikethrough", "superscript", "subscript"]],
//     ["para", ["ul", "ol", "paragraph"]],
//     ["insert", ["link"]],
//     ["view", ["fullscreen", "codeview", "help"]],
//   ],
//   popover: {
//     image: [],
//     link: [],
//     air: [],
//   },
// });

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

  // Ajax request
  $.ajax({
    url: `/dashboard/book/${bookId}/details`,
    method: "GET",
    success: function (response) {
      // Buat HTML untuk menampilkan data
      let html = "";

      // Tambahkan deskripsi jika ada
      if (response.description) {
        html += `
                    <div class="mb-4">
                        <h4 class="text-lg font-semibold mb-2 text-gray-900 dark:text-white">Description</h4>
                        <p class="text-gray-600 dark:text-gray-300">${response.description}</p>
                    </div>
                `;
      }

      // Tambahkan daftar isi jika ada
      if (response.table_of_contents && response.table_of_contents.length > 0) {
        html += `
                    <div>
                        <h4 class="text-lg font-semibold mb-2 text-gray-900 dark:text-white">Table of Contents</h4>
                        <ul class="list-disc pl-5 text-gray-600 dark:text-gray-300">
                `;

        response.table_of_contents.forEach((item) => {
          html += `<li>${item}</li>`;
        });

        html += `
                        </ul>
                    </div>
                `;
      }

      // Jika tidak ada data
      if (
        !response.description &&
        (!response.table_of_contents || response.table_of_contents.length === 0)
      ) {
        html =
          '<p class="text-gray-600 dark:text-gray-300">No detailed information available.</p>';
      }

      // Masukkan HTML ke dalam modal
      modalBody.html(html);
    },
    error: function (xhr, status, error) {
      // Handle error
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
