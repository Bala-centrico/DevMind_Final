import os
import sqlite3
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

DB_DIR = r"\\nas3be\ITCrediti\DevMind"
DB_FILE = os.path.join(DB_DIR, "oracle_standards.db")

# Ensure directory exists
os.makedirs(DB_DIR, exist_ok=True)

# ============================================================
# CONNECT TO SQLITE
# ============================================================

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
print(f"✅ Connected to SQLite DB: {DB_FILE}")

# ============================================================
# CREATE TABLES
# ============================================================

cursor.executescript("""
CREATE TABLE IF NOT EXISTS oracle_standards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    procedure_name TEXT NOT NULL UNIQUE,
    description TEXT,
    parameters TEXT,
    usage_example TEXT,
    created_on TEXT
);

CREATE TABLE IF NOT EXISTS sample_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_type TEXT,
    template_name TEXT UNIQUE,
    template_sql TEXT,
    description TEXT,
    created_on TEXT
);
""")
print("✅ Tables created successfully.")

# ============================================================
# INSERT ORGANIZATION ORACLE STANDARDS (IF NOT EXISTS)
# ============================================================

standards_data = [
    (
        "COFS",
        "Creates or forgets synonyms. If synonym exists, does nothing.",
        """P_OWNER: Owner of synonym (PUBLIC, WEBLOGIC, etc.)
P_SYNONYM_NAME: Synonym name
P_TABLE_OWNER: Owner of the base table
P_TABLE_NAME: Table name for which synonym is created
P_DEBUG: Used for debug; prints without executing""",
        """STD_PKG_ANTUTIL.COFS('PUBLIC', '{COMPONENT}_TR_CUSTOMER_DUMMY', 'WEBLOGIC_DBA', '{COMPONENT}_TR_CUSTOMER_DUMMY');""",
    ),
    (
        "DOFO",
        "Drops or forgets objects. If object exists, it drops it; otherwise does nothing.",
        """P_OWNER: Object owner (WEBLOGIC_DBA, etc.)
P_OBJECT_TYPE: FUNCTION, INDEX, PACKAGE, PROCEDURE, SEQUENCE, TRIGGER, VIEW, SYNONYM
P_OBJECT_NAME: Object name
P_DEBUG: Used for debug; prints without executing""",
        """BEGIN STD_PKG_ANTUTIL.DOFO('WEBLOGIC_DBA', 'SEQUENCE', '{COMPONENT}_SQ_DUM_CD_ID'); END;/""",
    ),
    (
        "DOFT",
        "Drops or forgets tables. If table exists, it drops it; otherwise does nothing.",
        """P_OWNER: Table owner (WEBLOGIC_DBA, etc.)
P_TABLE_NAME: Table name
P_CASCADE: Y/N; cascades constraints
P_DEBUG: Used for debug; prints without executing""",
        """BEGIN STD_PKG_ANTUTIL.DOFT('WEBLOGIC_DBA', '{COMPONENT}_TR_CUSTOMER_DUMMY', 'Y'); END;/""",
    ),
    (
        "DO_GRANT",
        "Gives grants on objects to specified users or roles.",
        """P_OWNER: Owner of object
P_OBJECT_NAME: Object name
P_GRANTEE: User/role to grant access
P_PRIVILEGE: SELECT,INSERT,UPDATE,DELETE,EXECUTE, etc.
P_GRANT_OPTION: Y/N; allows further grant
P_ENVIRONMENT: TEST, PREPROD, PROD (optional)
P_DEBUG: Debug only""",
        """BEGIN
    STD_PKG_ANTUTIL.DO_GRANT('WEBLOGIC_DBA', '{COMPONENT}_TR_ACCOUNT_DUMMY', 'UNIV_ORA', 'SELECT,INSERT,UPDATE,DELETE');
END;/""",
    ),
    (
        "DO_REVOKE",
        "Revokes given grants from specified users or roles.",
        """P_OWNER: Owner of object
P_OBJECT_NAME: Object name
P_GRANTEE: User/role from which grant revoked
P_PRIVILEGE: Privilege revoked
P_ENVIRONMENT: TEST, PREPROD, PROD
P_DEBUG: Debug only""",
        """BEGIN
    STD_PKG_ANTUTIL.DO_REVOKE('WEBLOGIC_DBA', '{COMPONENT}_TR_ACCOUNT_DUMMY', 'UNIV_ORA', 'SELECT,INSERT,UPDATE,DELETE');
END;/""",
    ),
]

for s in standards_data:
    cursor.execute("SELECT 1 FROM oracle_standards WHERE procedure_name = ?", (s[0],))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO oracle_standards (procedure_name, description, parameters, usage_example, created_on)
            VALUES (?, ?, ?, ?, ?)
        """, (s[0], s[1], s[2], s[3], datetime.now().isoformat()))
print(f"✅ Oracle standards inserted (if not already present).")

# ============================================================
# INSERT BASE TEMPLATES (IF NOT EXISTS)
# ============================================================

templates = [
    (
        "TABLE",
        "Base Table Creation Template",
        """CREATE TABLE {COMPONENT}_TR_{ENTITY}_DUMMY (
    {ENTITY_SHORT}_ID NUMBER,
    {ENTITY_SHORT}_NAME VARCHAR2(100),
    CREATED_DATE DATE DEFAULT SYSDATE,
    CONSTRAINT {COMPONENT}_DUM_{ENTITY_SHORT}_ID_PK PRIMARY KEY ({ENTITY_SHORT}_ID)
)
TABLESPACE @@TB_DATI_BIG@@
PCTFREE 10 PCTUSED 80;""",
        "Standard structure for new tables following naming conventions and storage rules."
    ),
    (
        "SEQUENCE",
        "Base Sequence Template",
        """CREATE SEQUENCE WEBLOGIC_DBA.{COMPONENT}_SQ_{ENTITY_SHORT}_ID
START WITH 1
INCREMENT BY 1
NOCACHE;""",
        "Standard sequence creation for table primary key columns."
    ),
    (
        "INDEX",
        "Base Index Template",
        """CREATE INDEX {COMPONENT}_IDX_{ENTITY_SHORT}_{COLUMN_SHORT}
ON {COMPONENT}_TR_{ENTITY}_DUMMY ({COLUMN_SHORT})
TABLESPACE @@TB_IDX_BIG@@
PCTFREE 10;""",
        "Standard index creation on key columns following naming conventions."
    )
]

for t in templates:
    cursor.execute("SELECT 1 FROM sample_templates WHERE template_name = ?", (t[1],))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO sample_templates (object_type, template_name, template_sql, description, created_on)
            VALUES (?, ?, ?, ?, ?)
        """, (t[0], t[1], t[2], t[3], datetime.now().isoformat()))
print(f"✅ Base templates inserted (if not already present).")

# ============================================================
# INSERT FULL CMU_TR_CUSTOMER_DUMMY SCRIPT (IF NOT EXISTS)
# ============================================================

cmu_sample_script = """
BEGIN
    STD_PKG_ANTUTIL.DOFT('WEBLOGIC_DBA', 'CMU_TR_CUSTOMER_DUMMY', 'Y');
    STD_PKG_ANTUTIL.DOFO('WEBLOGIC_DBA', 'SEQUENCE', 'CMU_SQ_DUM_CD_ID');
END;
/


CREATE TABLE CMU_TR_CUSTOMER_DUMMY (
    CD_ID              NUMBER,
    CD_CUSTOMER_ID     NUMBER,
    CD_CUSTOMER_NAME   VARCHAR2(100),
    CD_DATE_OF_BIRTH   DATE,
    CD_ADDRESS         VARCHAR2(200),
    CD_PHONE_NUMBER    VARCHAR2(15),
    CONSTRAINT CMU_DUM_CD_ID_PK_101 PRIMARY KEY (CD_ID),
    CONSTRAINT CMU_DUM_CD_CUSTOMER_ID_UK_1001 UNIQUE KEY (CD_CUSTOMER_ID)
)
TABLESPACE @@TB_DATI_BIG@@
PCTFREE 10 PCTUSED 80
/ 

COMMENT ON COLUMN CMU_TR_CUSTOMER_DUMMY.CD_ID IS 'Sequence ID for customer dummy table'
/
COMMENT ON COLUMN CMU_TR_CUSTOMER_DUMMY.CD_CUSTOMER_ID IS 'Unique customer identifier'
/
COMMENT ON COLUMN CMU_TR_CUSTOMER_DUMMY.CD_CUSTOMER_NAME IS 'Full name of the customer'
/
COMMENT ON COLUMN CMU_TR_CUSTOMER_DUMMY.CD_DATE_OF_BIRTH IS 'Customer date of birth'
/
COMMENT ON COLUMN CMU_TR_CUSTOMER_DUMMY.CD_ADDRESS IS 'Customer residential address'
/
COMMENT ON COLUMN CMU_TR_CUSTOMER_DUMMY.CD_PHONE_NUMBER IS 'Customer contact phone number'
/

CREATE INDEX CMU_IDX_DUM_CD_CUSTOMER_ID ON CMU_TR_CUSTOMER_DUMMY (CD_CUSTOMER_ID)
TABLESPACE @@TB_IDX_BIG@@
PCTFREE 10
/

CREATE SEQUENCE WEBLOGIC_DBA.CMU_SQ_DUM_CD_ID START WITH 1 INCREMENT BY 1 NOCACHE
/

BEGIN
    STD_PKG_ANTUTIL.DO_GRANT('WEBLOGIC_DBA', 'CMU_TR_CUSTOMER_DUMMY', 'UNIV_ORA', 'SELECT,INSERT,UPDATE,DELETE');
    STD_PKG_ANTUTIL.DO_GRANT('WEBLOGIC_DBA', 'CMU_TR_CUSTOMER_DUMMY', 'ANOMALIA_CREDITI', 'SELECT,INSERT,UPDATE,DELETE');
    STD_PKG_ANTUTIL.DO_GRANT('WEBLOGIC_DBA', 'CMU_TR_CUSTOMER_DUMMY', 'CONSULTA_COM', 'SELECT');
    STD_PKG_ANTUTIL.DO_GRANT('WEBLOGIC_DBA', 'CMU_TR_CUSTOMER_DUMMY', 'CONSULTA_AF', 'SELECT');
    STD_PKG_ANTUTIL.DO_GRANT('WEBLOGIC_DBA', 'CMU_TR_CUSTOMER_DUMMY', 'WLROLE', 'SELECT');
    STD_PKG_ANTUTIL.DO_GRANT('WEBLOGIC_DBA', 'CMU_TR_CUSTOMER_DUMMY', 'WEBLOGIC81', 'SELECT');
    STD_PKG_ANTUTIL.COFS('PUBLIC', 'CMU_TR_CUSTOMER_DUMMY', 'WEBLOGIC_DBA', 'CMU_TR_CUSTOMER_DUMMY');
    STD_PKG_ANTUTIL.COFS('PUBLIC', 'CMU_SQ_DUM_CD_ID', 'WEBLOGIC_DBA', 'CMU_SQ_DUM_CD_ID');
END;
/
"""

cursor.execute("SELECT 1 FROM sample_templates WHERE template_name = ?", ("CMU_TR_CUSTOMER_DUMMY Sample Script",))
if not cursor.fetchone():
    cursor.execute("""
        INSERT INTO sample_templates (object_type, template_name, template_sql, description, created_on)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "FULL_TABLE_SCRIPT",
        "CMU_TR_CUSTOMER_DUMMY Sample Script",
        cmu_sample_script,
        "Full Oracle sample table creation script with sequences, indexes, comments, and grants.",
        datetime.now().isoformat()
    ))
print("✅ Full CMU_TR_CUSTOMER_DUMMY script inserted (if not already present).")

# ============================================================
# VERIFICATION
# ============================================================

cursor.execute("SELECT procedure_name, description FROM oracle_standards")
print("\n📘 Oracle Standards:")
for row in cursor.fetchall():
    print(" -", row[0], ":", row[1])

cursor.execute("SELECT object_type, template_name FROM sample_templates")
print("\n📗 Templates:")
for row in cursor.fetchall():
    print(" -", row[0], ":", row[1])

conn.commit()
conn.close()
print("\n✅ Oracle Standards DB initialized successfully!")
