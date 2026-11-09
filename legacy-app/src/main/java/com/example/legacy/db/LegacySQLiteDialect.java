package com.example.legacy.db;

import org.hibernate.dialect.Dialect;
import org.hibernate.dialect.identity.IdentityColumnSupport;
import org.hibernate.dialect.identity.IdentityColumnSupportImpl;

import java.sql.Types;

/**
 * Hand-written SQLite dialect, added years ago because Hibernate never shipped one for this version.
 * Kept in the codebase and untouched since — the kind of file nobody dares upgrade.
 */
public class LegacySQLiteDialect extends Dialect {

    public LegacySQLiteDialect() {
        registerColumnType(Types.BIT, "integer");
        registerColumnType(Types.INTEGER, "integer");
        registerColumnType(Types.BIGINT, "integer");
        registerColumnType(Types.SMALLINT, "integer");
        registerColumnType(Types.VARCHAR, "text");
        registerColumnType(Types.NUMERIC, "numeric");
        registerColumnType(Types.DECIMAL, "numeric");
        registerColumnType(Types.TIMESTAMP, "text");
        registerColumnType(Types.BOOLEAN, "integer");
    }

    @Override
    public boolean hasAlterTable() {
        return false;
    }

    @Override
    public boolean dropConstraints() {
        return false;
    }

    @Override
    public String getAddColumnString() {
        return "add column";
    }

    @Override
    public IdentityColumnSupport getIdentityColumnSupport() {
        return new IdentityColumnSupportImpl() {
            @Override
            public boolean supportsIdentityColumns() {
                return true;
            }

            @Override
            public String getIdentitySelectString(String table, String column, int type) {
                return "select last_insert_rowid()";
            }

            @Override
            public String getIdentityColumnString(int type) {
                return "integer";
            }
        };
    }
}
