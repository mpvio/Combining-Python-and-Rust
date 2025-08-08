use std::{collections::HashMap, fs::File, io::{Seek, SeekFrom, Write}, process::{Command, Stdio}};

use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct Person {
    pub name: String,
    pub age: u8,
    pub ls: Vec::<String>,
    sentence: String
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(untagged)]
pub enum CleanDiffs {
    Str(String),
    Arr(Vec::<String>)
}

// impl Serialize for CleanDiffs {
//     fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
//     where
//         S: serde::Serializer {
//         match self {
//             CleanDiffs::Str(s) => s.serialize(serializer),
//             CleanDiffs::Arr(items) => items.serialize(serializer),
//         }
//     }
// }

fn main() {
    let v : Vec::<String> = vec!["ab".into(), "bc".into(), "cd".into()];
    let al = Person {
        name: "Alice".into(),
        age: 10,
        ls: v,
        sentence: "cat in a hat".into()
    };
    let bob = Person {
        name: "Robert".into(),
        age: 12,
        ls: vec!["ab".into()],
        sentence: "owl in a cowl".into()
    };
    // println!("{al:#?}, {bob:#?}");
    let res = python_stuff(al, bob);
    match res {
        Ok(r) => {
            println!("{r:#?}");
            save_to_file(r);
        },
        Err(e) => {
            println!("ERROR: {e:#?}");
        },
    }
}

fn save_to_file(res: HashMap<String, CleanDiffs>) {
    let name = "sample.json";
    if let Ok(mut file) = File::options().write(true).create(true).open(name) {
        let _ = file.set_len(0);
        let _ = file.seek(SeekFrom::Start(0));
        match serde_json::to_writer_pretty(file, &res) {
            Ok(_) => {
                println!("Success!");
            },
            Err(err) => {
                println!("{:#?}", err);
            },
        }
    }
}

fn python_stuff(a: Person, b: Person) -> Result<HashMap<String, CleanDiffs>, Box<dyn std::error::Error>> {

    let input = serde_json::json!({
        "a": a,
        "b": b
    }).to_string();

    // spawn python process
    let mut cmd = Command::new("python")
        .arg("src/comparer.py")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()?;

    // write json to stdin
    if let Some(ref mut stdin) = cmd.stdin {
        stdin.write_all(input.as_bytes())?;
    }

    // wait for python and capture output
    let output = cmd.wait_with_output()?;
    if !output.status.success() {
        return Err(format!(
            "Python failed: {}",
            String::from_utf8_lossy(&output.stderr)
        ).into());
    }

    // parse output to struct
    let result: HashMap<String, CleanDiffs> = serde_json::from_slice(&output.stdout)?;

    // return
    Ok(result)
}