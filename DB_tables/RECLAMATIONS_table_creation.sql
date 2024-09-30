use CSIData;
CREATE TABLE reclamations (
    id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT,
    text NVARCHAR(MAX),
    status NVARCHAR(50),
	screenshot_path NVARCHAR(255),
	created_at DATETIME2(0) DEFAULT SYSDATETIME(),
    CONSTRAINT FK_user_id FOREIGN KEY (user_id) REFERENCES users(id)
);