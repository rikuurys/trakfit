// Dummy student data
    const students = [
        {
            id: 1,
            name: "Juan D. Dela Cruz",
            section: "BSIT 1A-G1",
            age: 21,
            sex: "Male",
            email: "juandelacruz@gmail.com",
            lastUpdate: "3 Hours Ago"
        },
        {
            id: 2,
            name: "Maria Santos",
            section: "BSIT 1A-G1",
            age: 20,
            sex: "Female",
            email: "maria.santos@gmail.com",
            lastUpdate: "1 Hour Ago"
        },
        {
            id: 3,
            name: "Carlos Rodriguez",
            section: "BSIT 1A-G2",
            age: 22,
            sex: "Male",
            email: "carlos.rodriguez@gmail.com",
            lastUpdate: "Yesterday"
        },
        {
            id: 4,
            name: "Ana Gutierrez",
            section: "BSIT 1B-G1",
            age: 19,
            sex: "Female",
            email: "ana.gutierrez@gmail.com",
            lastUpdate: "5 Hours Ago"
        },
        {
            id: 5,
            name: "Miguel Fernandez",
            section: "BSIT 1B-G2",
            age: 21,
            sex: "Male",
            email: "miguel.fernandez@gmail.com",
            lastUpdate: "2 Days Ago"
        },
        {
            id: 6,
            name: "Sofia Martinez",
            section: "BSIT 1C-G1",
            age: 20,
            sex: "Female",
            email: "sofia.martinez@gmail.com",
            lastUpdate: "4 Days Ago"
        },
        {
            id: 7,
            name: "Liam Garcia",
            section: "BSIT 1D-G1",
            age: 23,
            sex: "Male",
            email: "liam.garcia@gmail.com",
            lastUpdate: "6 Hours Ago"
        },
        {
            id: 8,
            name: "Ella Cruz",
            section: "BSIT 1D-G2",
            age: 19,
            sex: "Female",
            email: "ella.cruz@gmail.com",
            lastUpdate: "Today"
        },
        {
            id: 9,
            name: "Noah Reyes",
            section: "BSIT 1E-G1",
            age: 21,
            sex: "Male",
            email: "noah.reyes@gmail.com",
            lastUpdate: "5 Days Ago"
        },
        {
            id: 10,
            name: "Isabella Flores",
            section: "BSIT 1E-G2",
            age: 20,
            sex: "Female",
            email: "isabella.flores@gmail.com",
            lastUpdate: "3 Hours Ago"
        },
        {
            id: 11,
            name: "Shawn Silvino",
            section: "BSIT 1E-G2",
            age: 20,
            sex: "Male",
            email: "shawn.silvino@gmail.com",
            lastUpdate: "3 Hours Ago"
        }
    ];

    // Render student rows dynamically
    const tableBody = document.getElementById('student-table-body');
    tableBody.innerHTML = students.map((student, index) => `
        
        <tr class="student-row" data-student-id="${student.id}" style="background-color: ${index % 2 === 1 ? '#f8f9fa' : '#ffffff'};">
            <td><input type="checkbox" class="student-checkbox" onclick="event.stopPropagation()"></td>
            <td><div class="student-avatar"></div></td>
            <td>
                <div class="student-info">
                    <div>
                        <h6 class="student-name">${student.name}</h6>
                        <div class="student-section">${student.section}</div>
                    </div>
                </div>
            </td>
            <td style="text-align: center;">
                <span class="student-labelInfo">${student.age}</span>
            </td>
            <td style="text-align: center;">
                <span class="student-labelInfo">${student.sex}</span>
            </td>
            <td style="text-align: center;">
                <div class="student-labelInfo">${student.email}</div>
            </td>
            <td style="text-align: center;">
                <div class="student-labelInfo">${student.lastUpdate}</div>
            </td>
        </tr>
    `).join('');

    // Search functionality
    document.querySelector('.search-input').addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        document.querySelectorAll('.student-row').forEach(row => {
            const name = row.querySelector('.student-name').textContent.toLowerCase();
            const section = row.querySelector('.student-section').textContent.toLowerCase();
            const email = row.querySelector('.student-labelInfo').textContent.toLowerCase();
            row.style.display = (name.includes(searchTerm) || section.includes(searchTerm) || email.includes(searchTerm)) ? '' : 'none';
        });
    });

    // Row click redirect
    document.addEventListener('click', e => {
        if (e.target.closest('.student-row')) {
            const studentId = e.target.closest('.student-row').dataset.studentId;
            window.location.href = `/student-profile/${studentId}/`;
        }
    });