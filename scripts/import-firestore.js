#!/usr/bin/env node

/**
 * Script pour importer des données JSON dans Firestore
 *
 * Usage:
 *   node scripts/import-firestore.js <collection> <json-file> [credentials-file] [--clean]
 *
 * Options:
 *   --clean    Supprime tous les documents existants avant d'importer
 *
 * Exemples:
 *   node scripts/import-firestore.js parties firebase/firestore_data/dev/parties.json
 *   node scripts/import-firestore.js parties firebase/firestore_data/dev/parties.json --clean
 */

const admin = require('firebase-admin');
const fs = require('fs');
const path = require('path');

// Parse arguments
const args = process.argv.slice(2);
const cleanFlag = args.includes('--clean');
const filteredArgs = args.filter(a => a !== '--clean');

if (filteredArgs.length < 2) {
  console.error('Usage: node scripts/import-firestore.js <collection> <json-file> [credentials-file] [--clean]');
  console.error('');
  console.error('Options:');
  console.error('  --clean    Delete all existing documents before importing');
  console.error('');
  console.error('Examples:');
  console.error('  node scripts/import-firestore.js parties firebase/firestore_data/dev/parties.json');
  console.error('  node scripts/import-firestore.js parties firebase/firestore_data/dev/parties.json --clean');
  process.exit(1);
}

const collectionName = filteredArgs[0];
const jsonFile = filteredArgs[1];
const credentialsFile = filteredArgs[2] || findCredentialsFile();

function findCredentialsFile() {
  // Look for Firebase credentials file in current directory
  const files = fs.readdirSync('.');
  const credFile = files.find(f => f.includes('firebase-adminsdk') && f.endsWith('.json'));
  if (credFile) {
    return credFile;
  }
  console.error('Error: No Firebase credentials file found. Please specify one.');
  process.exit(1);
}

// Validate files exist
if (!fs.existsSync(jsonFile)) {
  console.error(`Error: JSON file not found: ${jsonFile}`);
  process.exit(1);
}

if (!fs.existsSync(credentialsFile)) {
  console.error(`Error: Credentials file not found: ${credentialsFile}`);
  process.exit(1);
}

// Initialize Firebase Admin
const serviceAccount = require(path.resolve(credentialsFile));

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

async function deleteCollection(collectionRef) {
  const snapshot = await collectionRef.get();

  if (snapshot.empty) {
    console.log('  📭 Collection is empty, nothing to delete');
    return 0;
  }

  const batch = db.batch();
  let count = 0;

  snapshot.docs.forEach((doc) => {
    batch.delete(doc.ref);
    console.log(`  🗑️  Deleting ${doc.id}`);
    count++;
  });

  await batch.commit();
  return count;
}

async function importData() {
  console.log(`📂 Reading ${jsonFile}...`);
  const data = JSON.parse(fs.readFileSync(jsonFile, 'utf8'));

  // Clean collection if --clean flag is set
  if (cleanFlag) {
    console.log(`\n🧹 Cleaning collection "${collectionName}"...`);
    const deletedCount = await deleteCollection(db.collection(collectionName));
    console.log(`  Deleted ${deletedCount} documents\n`);
  }

  console.log(`📤 Importing to collection "${collectionName}"...`);

  const batch = db.batch();
  let count = 0;

  for (const [docId, docData] of Object.entries(data)) {
    // Skip template/readme entries
    if (docId.startsWith('_')) {
      console.log(`  ⏭️  Skipping ${docId}`);
      continue;
    }

    const docRef = db.collection(collectionName).doc(docId);
    batch.set(docRef, docData, { merge: false }); // Replace entirely, don't merge
    console.log(`  ✅ ${docId}`);
    count++;
  }

  await batch.commit();
  console.log(`\n🎉 Successfully imported ${count} documents to "${collectionName}"`);
}

importData()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error('❌ Error importing data:', error);
    process.exit(1);
  });
