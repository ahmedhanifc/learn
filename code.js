
function MyButton() {
    return (
        <button>I'm a button</button>
    )
}

// export default keyword specifies the default export of a module. A module can have only one default export
export default function MyApp() {
    return (
        <div>
            <h1> Welcome to My App</h1>
            <MyButton />
            {/*  MyButton starts with a capital letter. Thats how it is a react component.*/}
        </div>
    )
}
// the above syntax is called JSX. More stricted than HTML

